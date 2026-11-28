# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# Copyright (C) 2024 - TODAY Antônio S. P. Neto - Engenere
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import base64
import importlib.util
import logging
import os
from unittest import mock

from odoo.exceptions import UserError
from odoo.fields import Datetime

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
)
from odoo.addons.l10n_br_nfe.models.document import NFe

from .mock_utils import nfe_mock
from .test_nfe_serialize import TestNFeExport

_logger = logging.getLogger(__name__)


class TestNFeWebServices(TestNFeExport):
    @classmethod
    def setUpClass(cls):
        nfe_list = [
            {
                "record_ref": "l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11",
                "xml_file": "NFe35200159594315000157550010000000022062777169.xml",
            },
        ]
        super().setUpClass(nfe_list)

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
        }
    )
    def test_send_revalidates_stale_xml_error(self):
        """A document fixed after a failed validation must be transmittable
        again: the send re-validates against the current data instead of
        blocking on the stored (now stale) ``xml_error_message``."""
        nfe = self.nfe_list[0]["nfe"]
        # Simulate a validation error stored by an earlier confirm with bad
        # data, while the document's current data is in fact valid.
        nfe.xml_error_message = "stale validation error from a previous confirm"
        nfe.action_document_send()
        self.assertFalse(nfe.xml_error_message)
        self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
            "nfeRecepcaoEvento": "retEnvEvento/nfe_cancelamento.xml",
        }
    )
    def test_enviar_e_cancelar(self):
        for nfe_data in self.nfe_list:
            nfe = nfe_data["nfe"]

            nfe.action_document_send()

            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)

            cancel_wizard = (
                self.env["l10n_br_fiscal.document.cancel.wizard"]
                .with_context(active_model="l10n_br_fiscal.document", active_id=nfe.id)
                .create(
                    {"document_id": nfe.id, "justification": "Era apenas um teste."}
                )
            )
            cancel_wizard.doit()

            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_CANCELADA)
            self.assertIsNotNone(nfe.cancel_event_id)
            self.assertEqual(nfe.cancel_event_id.state, "done")
            self.assertEqual(nfe.cancel_event_id.status_code, "135")
            self.assertEqual(
                nfe.cancel_event_id.response, "Evento registrado e vinculado a NF-e"
            )
            self.assertEqual(
                Datetime.to_string(nfe.cancel_event_id.protocol_date),
                "2023-07-05 19:52:52",
            )
            # The homologated cancellation marks the document as cancelled
            # for SPED purposes, and the SPED guard then refuses to take it
            # back to draft: its number and key were consumed at SEFAZ, so
            # re-sending them would be rejected as a duplicate (cStat 204).
            self.assertEqual(nfe.state_fiscal, SITUACAO_FISCAL_CANCELADO)
            with self.assertRaisesRegex(UserError, "SPED"):
                nfe._trigger_fsm("action_draft_fsm")
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_CANCELADA)

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
            "nfeRecepcaoEvento": "retEnvEvento/nfe_cancelamento_fora_prazo.xml",
        }
    )
    def test_enviar_e_cancelar_fora_prazo(self):
        """A cancellation homologated out of time (cStat 155) marks the
        document as extemporaneously cancelled, and the SPED guard refuses
        to take it back to draft all the same."""
        nfe = self.nfe_list[0]["nfe"]
        nfe.action_document_send()
        self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)

        cancel_wizard = (
            self.env["l10n_br_fiscal.document.cancel.wizard"]
            .with_context(active_model="l10n_br_fiscal.document", active_id=nfe.id)
            .create({"document_id": nfe.id, "justification": "Era apenas um teste."})
        )
        cancel_wizard.doit()

        self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_CANCELADA)
        self.assertEqual(nfe.cancel_event_id.status_code, "155")
        self.assertEqual(nfe.state_fiscal, SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO)
        with self.assertRaisesRegex(UserError, "SPED"):
            nfe._trigger_fsm("action_draft_fsm")
        self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_CANCELADA)

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
            "nfeRecepcaoEvento": "retEnvEvento/nfe_cancelamento_mt.xml",
        }
    )
    def test_cancel_protocol_date_other_timezone(self):
        """dhRegEvento at -04:00 (MT/AM) is stored in UTC, not as local time."""
        nfe = self.nfe_list[0]["nfe"]
        nfe.action_document_send()
        cancel_wizard = (
            self.env["l10n_br_fiscal.document.cancel.wizard"]
            .with_context(active_model="l10n_br_fiscal.document", active_id=nfe.id)
            .create({"document_id": nfe.id, "justification": "Era apenas um teste."})
        )
        cancel_wizard.doit()
        self.assertEqual(nfe.cancel_event_id.state, "done")
        self.assertEqual(
            Datetime.to_string(nfe.cancel_event_id.protocol_date),
            "2023-07-05 19:52:52",
        )

    @nfe_mock({"nfeInutilizacaoNF": "retInutNFe/nfe_inutilizacao.xml"})
    def test_inutilizar(self):
        nfe = self.nfe_list[0]["nfe"]
        inutilizar_wizard = (
            self.env["l10n_br_fiscal.invalidate.number.wizard"]
            .with_context(active_model="l10n_br_fiscal.document", active_id=nfe.id)
            .create({"document_id": nfe.id, "justification": "Era apenas um teste."})
        )
        inutilizar_wizard.doit()

    def test_inutilizar_client_certificate(self):
        """The NF-e and NFC-e number invalidation clients present the company
        certificate on the TLS connection, like the transmission ones: without
        a real certificate the SEFAZ refuses the connection (HTTP 403)."""
        self.env["ir.config_parameter"].sudo().set_param(
            "l10n_br_nfe.nfelib_soap_transmission", "True"
        )
        company = self.nfe_list[0]["nfe"].company_id
        module = "odoo.addons.l10n_br_nfe.models.invalidate_number"
        for code, client_name in (("55", "NfeClient"), ("65", "NfceClient")):
            invalidate = self.env["l10n_br_fiscal.invalidate.number"].new(
                {
                    "company_id": company.id,
                    "document_type_id": self.env.ref(
                        f"l10n_br_fiscal.document_{code}"
                    ).id,
                }
            )
            with mock.patch(f"{module}.{client_name}") as client:
                invalidate._edoc_processor()
            kwargs = client.call_args.kwargs
            # 18.0 keeps the PKCS#12 as a base64 Binary and decodes it before
            # handing it to the client (certificate.file/password are gone).
            self.assertEqual(
                kwargs["pkcs12_data"], base64.b64decode(company.certificate.content)
            )
            self.assertEqual(
                kwargs["pkcs12_password"], company.certificate.pkcs12_password
            )

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
        }
    )
    def test_nfe_consult_receipt(self):
        """
        Tests the asynchronous NFe transmission, separating the sending and
        the consultation into two distinct steps.
        """
        for nfe_data in self.nfe_list:
            nfe = nfe_data["nfe"]
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_A_ENVIAR)
            with mock.patch.object(NFe, "make_pdf"):
                # enable skip receipt consultation during the send action
                self.env.company.nfe_separate_async_process = True
                nfe.action_document_send()
            # Document has been sent, but the receipt has not been consulted yet,
            # meaning the authorization protocol has not been received.
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_ENVIADA)
            # Consult the receipt to receive the usage authorization.
            nfe._nfe_consult_receipt()
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
        }
    )
    @mock.patch("odoo.addons.l10n_br_nfe.models.document._logger")
    def test_nfe_consult_receipt_without_nfe_saved(self, mock_logger):
        """
        Tests the NF-e processing result query after deleting the sent nfe xml.
        """
        for nfe_data in self.nfe_list:
            nfe = nfe_data["nfe"]
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_A_ENVIAR)
            with mock.patch.object(NFe, "make_pdf"):
                # enable skip receipt consultation during the send action
                self.env.company.nfe_separate_async_process = True
                nfe.action_document_send()
            # Document has been sent, but the receipt has not been consulted yet,
            # meaning the authorization protocol has not been received.
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_ENVIADA)
            # Consult the receipt to receive the usage authorization.

            # Erase the sending_file
            nfe.send_file_id = False
            self.assertFalse(nfe.send_file_id)

            nfe._nfe_consult_receipt()
            mock_logger.info.assert_called_with(
                "NF-e data not found when trying to assemble the "
                "xml with the authorization protocol (nfeProc)"
            )
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)

    @nfe_mock({"nfeConsultaNF": "retConsSitNFe/autorizado.xml"})
    def test_nfe_consult(self):
        for nfe_data in self.nfe_list:
            nfe = nfe_data["nfe"]
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_A_ENVIAR)
            nfe._document_status()
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)

    def _assert_consult_cancelled(self, status_code, state_fiscal):
        """An NF-e found cancelled by the status query has no cancel event
        (e.g. the cancel response was lost and the retry got cStat 573), so
        only its fiscal state keeps the SPED guard from taking it back to
        draft and resending its consumed number and key."""
        nfe = self.nfe_list[0]["nfe"]
        nfe.action_document_send()
        self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        nfe._document_status()
        self.assertEqual(nfe.status_code, status_code)
        self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_CANCELADA)
        self.assertFalse(nfe.cancel_event_id)
        self.assertEqual(nfe.state_fiscal, state_fiscal)
        with self.assertRaisesRegex(UserError, "SPED"):
            nfe.action_document_back2draft()
        self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_CANCELADA)

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
            "nfeConsultaNF": "retConsSitNFe/cancelado.xml",
        }
    )
    def test_nfe_consult_cancelled(self):
        self._assert_consult_cancelled("101", SITUACAO_FISCAL_CANCELADO)

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
            "nfeConsultaNF": "retConsSitNFe/cancelado_fora_prazo.xml",
        }
    )
    def test_nfe_consult_cancelled_out_of_time(self):
        self._assert_consult_cancelled("151", SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO)

    def test_migration_cancel_state_fiscal(self):
        """The migration fills the fiscal state of the cancelled NF-e from
        the cStat of the homologated cancel event or, when there is none,
        from the cStat of the status query saved on the document."""
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "migrations",
            "18.0.7.12.5",
            "post-migration.py",
        )
        spec = importlib.util.spec_from_file_location("nfe_cancel_migration", path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        nfe = self.nfe_list[0]["nfe"]
        scenarios = [
            ("135", "done", "135", SITUACAO_FISCAL_CANCELADO),
            ("155", "done", "135", SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO),
            (False, False, "101", SITUACAO_FISCAL_CANCELADO),
            (False, False, "151", SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO),
            ("573", "wait", "151", SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO),
            (False, False, "100", False),
        ]
        for event_code, event_state, status_code, state_fiscal in scenarios:
            with self.subTest(event_code=event_code, status_code=status_code):
                event = self.env["l10n_br_fiscal.event"]
                if event_code:
                    event = event.create(
                        {
                            "type": "2",
                            "document_id": nfe.id,
                            "document_type_id": nfe.document_type_id.id,
                            "document_serie_id": nfe.document_serie_id.id,
                            "document_number": nfe.document_number or "1",
                            "company_id": nfe.company_id.id,
                            "status_code": event_code,
                        }
                    )
                    event.state = event_state
                nfe.write(
                    {
                        "state_edoc": SITUACAO_EDOC_CANCELADA,
                        "state_fiscal": False,
                        "status_code": status_code,
                        "cancel_event_id": event.id,
                    }
                )
                migration.fill_cancel_state_fiscal(self.env)
                self.assertEqual(nfe.state_fiscal, state_fiscal)
        # The migration entry point only delegates to it. Called undecorated:
        # outside the module loader, the openupgrade decorator logs an error.
        nfe.write({"state_fiscal": False, "status_code": "101"})
        migration.migrate.__wrapped__(self.env, "18.0.7.12.4")
        self.assertEqual(nfe.state_fiscal, SITUACAO_FISCAL_CANCELADO)
