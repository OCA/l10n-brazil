# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import json
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import MOCK_POST, TestSerproCommon, answer
from .test_integra_contador import CERTIFICATE_PATH, fake_certificate


@tagged("post_install", "-at_install")
class TestSerproFlow(TestSerproCommon):
    """The state machine: what each service does to the assessment."""

    def setUp(self):
        super().setUp()
        patcher = mock.patch(CERTIFICATE_PATH, side_effect=fake_certificate)
        self.addCleanup(patcher.stop)
        patcher.start()

    # ------------------------------------------------------------------
    # Closing the MIT
    # ------------------------------------------------------------------

    def test_closing_sends_the_layout_payload_plus_the_transmission_flag(self):
        with mock.patch(
            MOCK_POST,
            return_value=answer({"protocoloEncerramento": "abc==", "idApuracao": 9}),
        ) as post:
            self.mit.action_serpro_close_mit()
        sent = json.loads(post.call_args.kwargs["json"]["pedidoDados"]["dados"])
        self.assertEqual(
            sent["PeriodoApuracao"], {"MesApuracao": 7, "AnoApuracao": 2026}
        )
        self.assertIn("DadosIniciais", sent)
        self.assertIs(sent["TransmissaoImediata"], True)

    def test_closing_keeps_the_protocol_and_the_authority_id(self):
        with mock.patch(
            MOCK_POST,
            return_value=answer({"protocoloEncerramento": "abc==", "idApuracao": 9}),
        ):
            self.mit.action_serpro_close_mit()
        self.assertEqual(self.mit.serpro_protocol, "abc==")
        self.assertEqual(self.mit.serpro_assessment_id, "9")

    def test_immediate_transmission_lands_transmitted_and_active(self):
        with mock.patch(
            MOCK_POST, return_value=answer({"protocoloEncerramento": "abc=="})
        ):
            self.mit.action_serpro_close_mit()
        self.assertEqual(self.mit.state, "transmitted")
        self.assertEqual(self.mit.rfb_situation, "active")

    def test_without_immediate_transmission_it_stays_in_progress(self):
        self.mit.immediate_transmission = False
        with mock.patch(
            MOCK_POST, return_value=answer({"protocoloEncerramento": "abc=="})
        ) as post:
            self.mit.action_serpro_close_mit()
        sent = json.loads(post.call_args.kwargs["json"]["pedidoDados"]["dados"])
        self.assertIs(sent["TransmissaoImediata"], False)
        self.assertEqual(self.mit.state, "closed")
        self.assertEqual(self.mit.rfb_situation, "in_progress")

    def test_a_pendency_stops_the_transmission(self):
        """Never send what the authority is going to refuse."""
        self.mit.responsible_cpf = False
        with mock.patch(MOCK_POST) as post, self.assertRaises(UserError):
            self.mit.action_serpro_close_mit()
        post.assert_not_called()

    def test_a_draft_assessment_is_not_sent(self):
        self.mit.state = "draft"
        with mock.patch(MOCK_POST) as post, self.assertRaises(UserError):
            self.mit.action_serpro_close_mit()
        post.assert_not_called()

    def test_a_refusal_is_reported_and_does_not_move_the_state(self):
        """The refusal comes back as a notification, not as an exception.

        An exception would roll the transaction back and delete the log entry
        that explains the refusal.
        """
        refusal = answer(
            None,
            status=400,
            messages=[{"codigo": "[Erro-MIT]", "texto": "Apuracao ja encerrada."}],
        )
        with mock.patch(MOCK_POST, return_value=refusal):
            action = self.mit.action_serpro_close_mit()
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["type"], "danger")
        self.assertIn("Apuracao ja encerrada", action["params"]["message"])
        self.assertEqual(self.mit.state, "assessed")
        self.assertFalse(self.mit.serpro_protocol)

    def test_a_refusal_is_still_logged(self):
        """The failed call is the one support needs to see."""
        refusal = answer(
            None,
            status=400,
            messages=[{"codigo": "[Erro-MIT]", "texto": "Apuracao ja encerrada."}],
        )
        with mock.patch(MOCK_POST, return_value=refusal):
            self.mit.action_serpro_close_mit()
        transmission = self.env["l10n_br_dctfweb.transmission"].search(
            [("assessment_id", "=", self.mit.id)]
        )
        self.assertEqual(len(transmission), 1)
        self.assertFalse(transmission.success)
        self.assertIn("Apuracao ja encerrada", transmission.messages)

    # ------------------------------------------------------------------
    # Audit trail
    # ------------------------------------------------------------------

    def test_the_log_keeps_the_request_and_the_answer(self):
        with mock.patch(
            MOCK_POST, return_value=answer({"protocoloEncerramento": "abc=="})
        ):
            self.mit.action_serpro_close_mit()
        transmission = self.mit.transmission_ids
        self.assertEqual(transmission.service, "ENCAPURACAO314")
        self.assertEqual(transmission.endpoint, "Declarar")
        self.assertEqual(transmission.environment, "trial")
        self.assertTrue(transmission.billed)
        self.assertTrue(transmission.success)
        self.assertEqual(transmission.protocol, "abc==")
        self.assertIn("PeriodoApuracao", transmission.request)

    def test_the_log_never_keeps_a_credential(self):
        with mock.patch(
            MOCK_POST, return_value=answer({"protocoloEncerramento": "abc=="})
        ):
            self.mit.action_serpro_close_mit()
        stored = self.mit.transmission_ids.request
        self.assertNotIn("a-token", stored)
        self.assertNotIn("secret", stored)
        self.assertNotIn("Authorization", stored)

    def test_the_answer_reaches_the_chatter(self):
        with mock.patch(
            MOCK_POST, return_value=answer({"protocoloEncerramento": "abc=="})
        ):
            self.mit.action_serpro_close_mit()
        self.assertTrue(
            any(
                "Requisicao efetuada com sucesso" in str(message.body)
                for message in self.mit.message_ids
            )
        )

    # ------------------------------------------------------------------
    # Cost warning
    # ------------------------------------------------------------------

    def test_a_billed_call_asks_before_spending(self):
        self.company.sudo().serpro_warn_cost = True
        with mock.patch(MOCK_POST) as post:
            action = self.mit.action_serpro_close_mit()
        post.assert_not_called()
        self.assertEqual(action["res_model"], "l10n_br_dctfweb.cost.warning")
        self.assertEqual(action["context"]["default_service_key"], "close_assessment")

    def test_confirming_the_warning_runs_the_call(self):
        self.company.sudo().serpro_warn_cost = True
        wizard = self.env["l10n_br_dctfweb.cost.warning"].create(
            {"assessment_id": self.mit.id, "service_key": "close_assessment"}
        )
        self.assertEqual(wizard.service_name, "Close MIT assessment")
        with mock.patch(
            MOCK_POST, return_value=answer({"protocoloEncerramento": "abc=="})
        ) as post:
            wizard.action_confirm()
        post.assert_called_once()
        self.assertEqual(self.mit.state, "transmitted")

    def test_the_warning_can_be_turned_off_from_the_wizard(self):
        self.company.sudo().serpro_warn_cost = True
        wizard = self.env["l10n_br_dctfweb.cost.warning"].create(
            {"assessment_id": self.mit.id, "service_key": "close_assessment"}
        )
        with mock.patch(
            MOCK_POST, return_value=answer({"protocoloEncerramento": "abc=="})
        ):
            wizard.action_never_warn_again()
        self.assertFalse(self.company.sudo().serpro_warn_cost)

    def test_an_unbilled_call_never_asks(self):
        """Asking about a free call trains the user to click through."""
        self.company.sudo().serpro_warn_cost = True
        self.mit.serpro_protocol = "abc=="
        with mock.patch(
            MOCK_POST, return_value=answer({"situacaoEncerramento": "ENCERRADA"})
        ) as post:
            self.mit.action_serpro_closing_status()
        post.assert_called_once()
        self.assertEqual(self.mit.closing_status, "ENCERRADA")

    # ------------------------------------------------------------------
    # Asynchronous closing and the rest of the flow
    # ------------------------------------------------------------------

    def test_the_closing_status_needs_a_protocol(self):
        with self.assertRaises(UserError):
            self.mit.action_serpro_closing_status()

    def test_the_closing_status_reads_the_authority_id_when_it_finishes(self):
        self.mit.serpro_protocol = "abc=="
        with mock.patch(
            MOCK_POST,
            return_value=answer(
                {"situacaoEncerramento": "ENCERRADA", "idApuracao": 42}
            ),
        ):
            self.mit.action_serpro_closing_status()
        self.assertEqual(self.mit.serpro_assessment_id, "42")

    def test_while_it_is_running_no_id_is_written(self):
        self.mit.serpro_protocol = "abc=="
        with mock.patch(
            MOCK_POST,
            return_value=answer(
                {"situacaoEncerramento": "EM_ANDAMENTO", "idApuracao": 42}
            ),
        ):
            self.mit.action_serpro_closing_status()
        self.assertEqual(self.mit.closing_status, "EM_ANDAMENTO")
        self.assertFalse(self.mit.serpro_assessment_id)

    def test_the_period_data_is_what_the_dctfweb_services_take(self):
        self.assertEqual(
            self.mit._period_data(),
            {"categoria": "GERAL_MENSAL", "anoPA": "2026", "mesPA": "07"},
        )

    def test_transmitting_without_a_signed_xml_is_refused(self):
        self.mit.write({"state": "closed", "immediate_transmission": False})
        with mock.patch(MOCK_POST) as post, self.assertRaises(UserError):
            self.mit.action_serpro_transmit_dctfweb()
        post.assert_not_called()

    def test_transmitting_a_signed_xml_lands_the_receipt(self):
        self.mit.write(
            {
                "state": "closed",
                "immediate_transmission": False,
                "signed_declaration_xml": b"c2lnbmVk",
            }
        )
        with mock.patch(MOCK_POST, return_value=answer("12345")) as post:
            self.mit.action_serpro_transmit_dctfweb()
        sent = json.loads(post.call_args.kwargs["json"]["pedidoDados"]["dados"])
        self.assertEqual(sent["categoria"], "GERAL_MENSAL")
        self.assertTrue(sent["xmlAssinadoBase64"])
        self.assertEqual(self.mit.state, "transmitted")
        self.assertEqual(self.mit.receipt_number, "12345")

    def test_the_darf_of_a_declaration_in_progress_uses_its_own_service(self):
        self.mit.state = "closed"
        with mock.patch(MOCK_POST, return_value=answer({"pdf": "cGRm"})) as post:
            self.mit.action_serpro_issue_darf()
        service = post.call_args.kwargs["json"]["pedidoDados"]["idServico"]
        self.assertEqual(service, "GERARGUIAANDAMENTO313")
        self.assertTrue(self.mit.darf_file)
        self.assertIn("DARF", self.mit.darf_filename)

    def test_the_darf_of_a_transmitted_declaration_uses_the_plain_service(self):
        self.mit.state = "transmitted"
        with mock.patch(MOCK_POST, return_value=answer({"pdf": "cGRm"})) as post:
            self.mit.action_serpro_issue_darf()
        service = post.call_args.kwargs["json"]["pedidoDados"]["idServico"]
        self.assertEqual(service, "GERARGUIA31")

    def test_a_darf_without_a_document_is_reported(self):
        """A success that carries no document is still an answer to keep."""
        self.mit.state = "transmitted"
        with mock.patch(MOCK_POST, return_value=answer({})):
            action = self.mit.action_serpro_issue_darf()
        self.assertEqual(action["tag"], "display_notification")
        self.assertFalse(self.mit.darf_file)
        self.assertEqual(
            len(
                self.env["l10n_br_dctfweb.transmission"].search(
                    [("assessment_id", "=", self.mit.id)]
                )
            ),
            1,
        )

    def test_the_full_declaration_is_attached(self):
        self.mit.state = "transmitted"
        with mock.patch(MOCK_POST, return_value=answer({"pdf": "cGRm"})):
            self.mit.action_serpro_full_declaration()
        self.assertTrue(self.mit.full_declaration_file)
        self.assertTrue(self.mit.full_declaration_filename.endswith(".pdf"))

    def test_the_receipt_number_comes_back(self):
        self.mit.state = "transmitted"
        with mock.patch(MOCK_POST, return_value=answer({"numeroRecibo": "777"})):
            self.mit.action_serpro_receipt()
        self.assertEqual(self.mit.receipt_number, "777")

    def test_the_declaration_xml_is_attached(self):
        self.mit.state = "transmitted"
        with mock.patch(MOCK_POST, return_value=answer({"xml": "PHhtbC8+"})):
            self.mit.action_serpro_fetch_xml()
        self.assertTrue(self.mit.declaration_xml)
        self.assertTrue(self.mit.declaration_xml_filename.endswith(".xml"))

    def test_consulting_the_assessment_needs_the_authority_id(self):
        with self.assertRaises(UserError):
            self.mit.action_serpro_consult_assessment()

    def test_a_company_without_cnpj_is_refused_before_the_call(self):
        self.company.sudo().cnpj_cpf = False
        with mock.patch(MOCK_POST) as post, self.assertRaises(UserError):
            self.mit.action_serpro_close_mit()
        post.assert_not_called()
