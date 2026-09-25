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
        self.env["account.group"].search(
            [
                ("company_id", "=", self.company.root_id.id),
                ("l10n_br_dere_cta_ref", "!=", False),
            ]
        ).l10n_br_dere_cta_ref = False
        with self.assertRaises(UserError):
            declaration.action_generate_d1011()

    def test_missing_parent_account_is_rejected(self):
        declaration = self._create_declaration("2026-05")
        original = type(self.env["l10n_br_dere.table.period"])._pgcc_row_from_group

        def skip_parent(rec, group, codes):
            if group == self.parent_group:
                return False
            return original(rec, group, codes)

        with patch.object(
            type(self.env["l10n_br_dere.table.period"]),
            "_pgcc_row_from_group",
            skip_parent,
        ):
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
        self._accept_tables(declaration)
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
        self.assertEqual(declaration.state, "trial_ok")
        self.assertFalse(declaration.can_generate_trial)
        self.assertTrue(declaration.can_send_periodics)
        self.assertEqual(declaration.primary_action, "send_periodics")
        with self.assertRaises(UserError):
            declaration.action_mark_reopened()
        self._accept_closing(declaration)
        self.assertEqual(declaration.state, "closed")
        self.assertTrue(declaration.can_reopen_period)
        self.assertFalse(declaration.can_discard_local_closing)
        self.assertFalse(declaration.can_consult_results)
        declaration.action_mark_reopened()
        self.assertEqual(declaration.state, "closed")
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1198")
        self.assertTrue(event.xml_content)
        self.assertIn("<evtReabertMensal", event.xml_content)
        self.assertIn(self._closing_receipt("2026-02"), event.xml_content)
        self.assertTrue(event.event_id_attr.startswith("DeRE11981"))
        self.assertTrue(declaration.can_discard_local_reopening)
        self.assertTrue(declaration.can_send_periodics)
        self.assertEqual(declaration.primary_action, "send_periodics")
        declaration.action_mark_reopened()
        self.assertEqual(
            declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1198"),
            event,
        )
        with self.assertRaises(UserError):
            declaration.action_generate_d1101()
        self._accept_reopening(declaration)
        self.assertEqual(declaration.state, "reopened")
        self.assertFalse(declaration.can_discard_local_reopening)
        self.assertFalse(declaration.can_generate_trial)
        self.assertTrue(declaration.can_replace_trial)
        self.assertFalse(declaration.can_close_period)
        self.assertEqual(declaration.primary_action, "replace_trial")
        declaration.action_replace_d1101()
        replacement = declaration.event_ids.filtered(
            lambda ev: ev.event_type == "D-1101"
        ).sorted("id")[-1]
        self.assertEqual(replacement.tp_oper, "2")
        self.assertIn("<tpOper>2</tpOper>", replacement.xml_content)
        self.assertIn("<nrRecibo>", replacement.xml_content)
        self.assertEqual(declaration.state, "reopened")
        self.assertTrue(declaration.can_close_period)
        self.assertEqual(
            len(declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1101")),
            2,
        )

    def test_accepted_tables_lock_pgcc_snapshot(self):
        declaration = self._create_declaration("2026-02")
        declaration.action_generate_tables()
        line = declaration.pgcc_account_ids[:1]
        line.write({"dere12_nomeCta": "Draft edit"})
        self.assertEqual(line.dere12_nomeCta, "Draft edit")
        self._accept_tables(declaration)
        with self.assertRaises(UserError):
            line.write({"dere12_nomeCta": "Accepted edit"})
        with self.assertRaises(UserError):
            line.unlink()

    def test_closed_declaration_cannot_change_company_or_period(self):
        declaration = self._create_declaration("2026-03")
        self._post_entry("2026-03-10", self.receivable, self.fee_account, 50.0)
        declaration.action_generate_tables()
        self._accept_tables(declaration)
        declaration.action_generate_d1101()
        with self.assertRaises(UserError):
            declaration.write({"per_apur": "2026-06"})
        declaration.action_generate_d1199()
        self.assertEqual(declaration.state, "trial_ok")
        self._accept_closing(declaration)
        self.assertEqual(declaration.state, "closed")
        with self.assertRaises(UserError):
            declaration.write({"company_id": declaration.company_id.id})
        with self.assertRaises(UserError):
            declaration.write({"table_period_id": declaration.table_period_id.id})
        with self.assertRaises(UserError):
            declaration.write({"ind_inexist_dedu": True})
        with self.assertRaises(UserError):
            declaration.pgcc_account_ids[:1].write({"dere12_nomeCta": "X"})
        with self.assertRaises(UserError):
            declaration.trial_line_ids[:1].write({"dere12_vApur": 1})

    def test_processed_event_cannot_be_edited_or_deleted(self):
        declaration = self._create_declaration("2026-04")
        declaration.action_generate_d1001()
        event = self._event(declaration, "D-1001")
        event.write({"state": "accepted", "cd_retorno": "1"})
        with self.assertRaises(UserError):
            event.write({"tp_oper": "2"})
        with self.assertRaises(UserError):
            event.unlink()

    def test_generated_event_can_be_deleted(self):
        declaration = self._create_declaration("2026-05")
        declaration.action_generate_d1001()
        event = self._event(declaration, "D-1001")
        self.assertEqual(event.state, "generated")
        event.unlink()
        self.assertFalse(self._event(declaration, "D-1001"))

    def test_discard_local_closing_unlocks_generated_d1199(self):
        declaration = self._create_declaration("2026-07")
        declaration.action_generate_tables()
        self._post_entry("2026-07-10", self.receivable, self.fee_account, 10.0)
        declaration.action_generate_d1101()
        declaration.action_generate_d1199()
        self.assertEqual(declaration.state, "trial_ok")
        declaration.action_discard_local_closing()
        self.assertFalse(
            declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1199")
        )
        self.assertEqual(declaration.state, "trial_ok")
        self.assertFalse(declaration.can_discard_local_closing)
        declaration.action_generate_d1199()
        self.assertTrue(
            declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1199")
        )

    def test_discard_local_closing_heals_stale_closed_state(self):
        declaration = self._create_declaration("2026-08")
        declaration.action_generate_tables()
        self._post_entry("2026-08-10", self.receivable, self.fee_account, 10.0)
        declaration.action_generate_d1101()
        declaration.action_generate_d1199()
        declaration.write({"state": "closed"})
        self.assertTrue(declaration.can_discard_local_closing)
        self.assertFalse(declaration.can_reopen_period)
        with self.assertRaises(UserError):
            declaration.action_mark_reopened()
        declaration.action_discard_local_closing()
        self.assertEqual(declaration.state, "trial_ok")
        self.assertFalse(
            declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1199")
        )

    def test_local_closing_blocks_input_regeneration(self):
        declaration = self._create_declaration("2026-06")
        declaration.action_generate_tables()
        self._accept_tables(declaration)
        self._post_entry("2026-06-10", self.receivable, self.fee_account, 10.0)
        declaration.action_generate_d1101()
        declaration.action_generate_d1199()
        self.assertFalse(declaration.can_generate_trial)
        declaration.action_discard_local_closing()
        self.assertTrue(declaration.can_generate_trial)

    def test_discard_local_reopening_restores_closed_state(self):
        declaration = self._create_declaration("2026-12")
        declaration.action_generate_tables()
        self._post_entry("2026-12-10", self.receivable, self.fee_account, 10.0)
        declaration.action_generate_d1101()
        declaration.action_generate_d1199()
        self._accept_closing(declaration)
        declaration.action_mark_reopened()
        self.assertEqual(declaration.state, "closed")
        declaration.action_discard_local_reopening()
        self.assertEqual(declaration.state, "closed")
        self.assertFalse(
            declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1198")
        )
        self.assertFalse(declaration.can_discard_local_reopening)
        self.assertTrue(declaration.can_reopen_period)
        self.assertEqual(declaration.primary_action, "reopen")

    def test_discard_local_reopening_heals_stale_reopened_state(self):
        declaration = self._create_declaration("2025-09")
        declaration.action_generate_tables()
        self._post_entry("2025-09-10", self.receivable, self.fee_account, 10.0)
        declaration.action_generate_d1101()
        declaration.action_generate_d1199()
        self._accept_closing(declaration)
        declaration.action_mark_reopened()
        declaration.write({"state": "reopened"})
        self.assertTrue(declaration.can_discard_local_reopening)
        declaration.action_discard_local_reopening()
        self.assertEqual(declaration.state, "closed")

    def test_discard_official_d1198_is_blocked(self):
        declaration = self._create_declaration("2025-08")
        declaration.action_generate_tables()
        self._post_entry("2025-08-10", self.receivable, self.fee_account, 10.0)
        declaration.action_generate_d1101()
        declaration.action_generate_d1199()
        self._accept_closing(declaration)
        declaration.action_mark_reopened()
        self._accept_reopening(declaration)
        self.assertEqual(declaration.state, "reopened")
        with self.assertRaises(UserError):
            declaration.action_discard_local_reopening()

    def test_discard_local_reopening_without_event(self):
        declaration = self._create_declaration("2025-07")
        with self.assertRaises(UserError):
            declaration.action_discard_local_reopening()

    def test_discard_official_d1199_is_blocked(self):
        declaration = self._create_declaration("2026-09")
        declaration.action_generate_tables()
        self._post_entry("2026-09-10", self.receivable, self.fee_account, 10.0)
        declaration.action_generate_d1101()
        declaration.action_generate_d1199()
        self._accept_closing(declaration)
        with self.assertRaises(UserError):
            declaration.action_discard_local_closing()
        self.assertEqual(declaration.state, "closed")
        self.assertFalse(declaration.can_consult_results)

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
            try:
                action = declaration.action_send_tables()
            except UserError:
                return
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(self._event(declaration, "D-1001").state, "rejected")

    def test_regenerate_after_reject_creates_new_event(self):
        declaration = self._create_declaration("2025-10")
        declaration.action_generate_d1001()
        event = self._event(declaration, "D-1001")
        declaration.apply_return(event, "0", desc_retorno="Erro")
        self.assertTrue(declaration.can_generate_tables)
        declaration.action_generate_d1001()
        events = self._table_period(declaration).event_ids.filtered(
            lambda ev: ev.event_type == "D-1001"
        )
        self.assertEqual(len(events), 2)
        self.assertTrue(events.filtered(lambda ev: ev.state == "rejected"))
        self.assertTrue(events.filtered(lambda ev: ev.state == "generated"))

    def test_apply_return_xml_and_builder_errors(self):
        declaration = self._create_declaration("2025-11")
        declaration.action_generate_d1001()
        declaration.action_apply_return_xml(RETURN_D9001.encode())
        event = self._event(declaration, "D-1001")
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
