# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_dere.models import xml_builder

from .common import DereCommon
from .test_dere_transmit import RETURN_D9001, _FakeResponse


@tagged("post_install", "-at_install")
class TestDereErrors(DereCommon):
    def test_company_validations_on_d1001(self):
        declaration = self._create_declaration("2026-08")
        self.company.dere_reg_trib_princ = False
        with self.assertRaises(UserError):
            declaration.action_generate_d1001()
        self.company.dere_reg_trib_princ = "2"
        self.company.dere_reg_trib_secund = "2"
        with self.assertRaises(UserError):
            declaration.action_generate_d1001()
        self.company.dere_reg_trib_secund = False
        self.company.dere_activity_ids = [Command.clear()]
        self.company.dere_reg_trib_princ = "1"
        with self.assertRaises(UserError):
            declaration.action_generate_d1001()
        self.company.dere_reg_trib_princ = "3"
        with self.assertRaises(UserError):
            declaration.action_generate_d1001()

    def test_invalid_cnpj_root(self):
        declaration = self._create_declaration("2026-07")
        with patch.object(type(self.company), "_dere_cnpj_root", return_value="12"):
            with self.assertRaises(UserError):
                declaration.action_generate_d1001()

    def test_pgcc_requires_chart_and_accounts(self):
        declaration = self._create_declaration("2026-06")
        declaration.action_generate_d1001()
        self.company.dere_plano_cta_ref = False
        with self.assertRaises(UserError):
            declaration.action_generate_d1011()
        self.company.dere_plano_cta_ref = "4"
        self.company.dere_freq_encerr = False
        with self.assertRaises(UserError):
            declaration.action_generate_d1011()
        self.company.dere_freq_encerr = "M"
        self.env["account.account"].search(
            [
                ("company_ids", "in", self.company.ids),
                ("l10n_br_dere_cta_ref", "!=", False),
            ]
        ).l10n_br_dere_cta_ref = False
        with self.assertRaises(UserError):
            declaration.action_generate_d1011()

    def test_missing_parent_account_is_rejected(self):
        declaration = self._create_declaration("2026-05")
        self.parent_account.l10n_br_dere_cta_ref = False
        with self.assertRaises(UserError):
            declaration.action_generate_d1011()

    def test_trial_requires_movement(self):
        declaration = self._create_declaration("2026-04")
        declaration.action_generate_tables()
        with self.assertRaises(UserError):
            declaration.action_generate_d1101()

    def test_d1199_no_deductions_when_subject(self):
        declaration = self._create_declaration("2026-03")
        declaration.action_generate_tables()
        self._post_entry("2026-03-10", self.receivable, self.fee_account, 10.0)
        declaration.action_generate_d1101()
        self.company.dere_subject_d1121 = True
        declaration.ind_inexist_dedu = True
        declaration.action_generate_d1199()
        xml = declaration.event_ids.filtered(
            lambda ev: ev.event_type == "D-1199"
        ).xml_content
        self.assertIn("<indInexistDedu>1</indInexistDedu>", xml)

    def test_reopen_closed_period(self):
        declaration = self._create_declaration("2026-02")
        declaration.action_generate_tables()
        self._post_entry("2026-02-10", self.receivable, self.fee_account, 10.0)
        declaration.action_generate_d1101()
        declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1101").write(
            {
                "state": "accepted",
                "nr_recibo": "1101-202602-0000000000000000001",
                "cd_retorno": "1",
            }
        )
        declaration.action_generate_d1199()
        with self.assertRaises(UserError):
            declaration.action_mark_reopened()
        self._accept_closing(declaration)
        declaration.action_mark_reopened()
        self.assertEqual(declaration.state, "reopened")
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1198")
        self.assertTrue(event.xml_content)
        self.assertIn("<evtReabertMensal", event.xml_content)
        self.assertIn(self._closing_receipt("2026-02"), event.xml_content)
        self.assertTrue(event.event_id_attr.startswith("DeRE11982"))
        with self.assertRaises(UserError):
            declaration.action_mark_reopened()
        with self.assertRaises(UserError):
            declaration.action_generate_d1101()
        event.write({"state": "accepted", "cd_retorno": "1"})
        declaration.action_generate_d1101()
        self.assertEqual(
            len(declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1101")),
            2,
        )

    def test_send_without_events_or_token_error(self):
        declaration = self._create_declaration("2026-01")
        with self.assertRaises(UserError):
            declaration.action_send_tables()
        declaration.action_generate_d1001()
        with patch(
            "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
            return_value=_FakeResponse(status_code=401, text="unauthorized"),
        ):
            with self.assertRaises(UserError):
                declaration.action_send_tables()

    def test_send_without_certificate(self):
        declaration = self._create_declaration("2026-03")
        declaration.action_generate_d1001()
        self.company.certificate_nfe_id = False
        self.company.certificate_ecnpj_id = False
        with patch(
            "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
            return_value=_FakeResponse(),
        ) as mocked:
            with self.assertRaises(UserError) as error:
                declaration.action_send_tables()
            self.assertIn("A1", str(error.exception))
            mocked.assert_not_called()

    def test_send_batch_http_error(self):
        declaration = self._create_declaration("2025-12")
        declaration.action_generate_d1001()

        def fake_post(url, **_kwargs):
            if "token" in url:
                return _FakeResponse(
                    payload={"access_token": "tok", "expires_in": 3600}
                )
            return _FakeResponse(status_code=400, text="batch rejected")

        with patch(
            "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
            side_effect=fake_post,
        ):
            with self.assertRaises(UserError):
                declaration.action_send_tables()

    def test_regenerate_after_reject_creates_new_event(self):
        declaration = self._create_declaration("2025-10")
        declaration.action_generate_d1001()
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1001")
        declaration.apply_return(event, "0", desc_retorno="Erro")
        declaration.action_generate_d1001()
        events = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1001")
        self.assertEqual(len(events), 2)
        self.assertTrue(events.filtered(lambda ev: ev.state == "rejected"))
        self.assertTrue(events.filtered(lambda ev: ev.state == "generated"))

    def test_apply_return_xml_and_builder_errors(self):
        declaration = self._create_declaration("2025-11")
        declaration.action_generate_d1001()
        declaration.action_apply_return_xml(RETURN_D9001.encode())
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1001")
        self.assertEqual(event.state, "accepted")
        parsed = xml_builder.parse_return(RETURN_D9001.encode())
        self.assertEqual(parsed["tpEv"], "D-1001")
        with self.assertRaises(ValueError):
            xml_builder.build_d1001(
                {
                    "id": "x" * 42,
                    "tpOper": "1",
                    "tpAmb": "2",
                    "verAplic": "test",
                    "nrInsc": "12345678",
                    "iniValid": False,
                }
            )
