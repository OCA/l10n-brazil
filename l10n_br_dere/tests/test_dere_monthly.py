# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_dere.constants import STRUCTURED_EVENT_ID_RE

from .common import DereCommon


@tagged("post_install", "-at_install")
class TestDereMonthly(DereCommon):
    def test_d1101_continuity_and_zero_vapur(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._post_entry(
            "2026-09-30",
            self.receivable,
            self.equity_account,
            250.0,
            ref="Opening continuity",
        )
        self._post_entry(
            "2026-10-15",
            self.receivable,
            self.fee_account,
            1000.0,
            ref="Administration fee",
        )
        declaration.action_generate_d1101()
        self.assertEqual(declaration.state, "trial_ok")
        fee_line = declaration.trial_line_ids.filtered(
            lambda line: line.pgcc_account_id.account_id == self.fee_account
        )
        equity_line = declaration.trial_line_ids.filtered(
            lambda line: line.pgcc_account_id.account_id == self.equity_account
        )
        self.assertEqual(fee_line.account_name, self.fee_account.name)
        self.assertEqual(fee_line.dere12_vMovCred, 1000.0)
        self.assertEqual(fee_line.dere12_vApur, 1000.0)
        self.assertEqual(equity_line.dere12_vSaldoInic, 250.0)
        self.assertEqual(equity_line.dere12_vMovDebt, 0.0)
        self.assertEqual(equity_line.dere12_vMovCred, 0.0)
        self.assertEqual(equity_line.dere12_vApur, 0.0)
        root = etree.fromstring(
            declaration.event_ids.filtered(
                lambda ev: ev.event_type == "D-1101"
            ).xml_content.encode("utf-8")
        )
        self.assertEqual(root.findtext(".//{*}perApur"), "2026-10")
        event_id = root.find(".//{*}evtBalancete").get("id") or ""
        self.assertRegex(event_id, STRUCTURED_EVENT_ID_RE)
        self.assertTrue(event_id.startswith("DeRE11011"))
        self.assertIn(self.company._dere_cnpj_root().rjust(14, "0"), event_id)

    def test_d1101_fee_vs_pass_through(self):
        fee = self.env["account.account"].create(
            {
                "name": "Isolated administration fees",
                "code": "DERE4881",
                "account_type": "income",
                "company_ids": [Command.set(self.company.ids)],
                "l10n_br_dere_cta_interna": "4881",
                "l10n_br_dere_dbr_mista": "000",
                "l10n_br_dere_cta_ref": "120110006",
                "l10n_br_dere_nat_cta": "C",
                "l10n_br_dere_cod_nat": "4",
                "l10n_br_dere_cod_trib": self.tax_admin_fee.id,
            }
        )
        pass_through = self.env["account.account"].create(
            {
                "name": "Isolated operator pass-through",
                "code": "DERE2888",
                "account_type": "liability_payable",
                "reconcile": True,
                "company_ids": [Command.set(self.company.ids)],
                "l10n_br_dere_cta_interna": "2888",
                "l10n_br_dere_dbr_mista": "000",
                "l10n_br_dere_cta_ref": "2",
                "l10n_br_dere_nat_cta": "C",
                "l10n_br_dere_cod_nat": "2",
                "l10n_br_dere_cod_trib": self.tax_equity.id,
            }
        )
        declaration = self._create_declaration("2027-08")
        declaration.action_generate_tables()
        self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": "2027-08-15",
                "journal_id": self.journal.id,
                "company_id": self.company.id,
                "ref": "Isolated billing split",
                "line_ids": [
                    Command.create(
                        {
                            "account_id": self.receivable.id,
                            "name": "Billed",
                            "debit": 1250000.0,
                            "credit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": fee.id,
                            "name": "Fee",
                            "debit": 0.0,
                            "credit": 100000.0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": pass_through.id,
                            "name": "Pass-through",
                            "debit": 0.0,
                            "credit": 1150000.0,
                        }
                    ),
                ],
            }
        ).action_post()
        declaration.action_generate_d1101()
        fee_line = declaration.trial_line_ids.filtered(
            lambda line: line.pgcc_account_id.account_id == fee
        )
        pass_line = declaration.trial_line_ids.filtered(
            lambda line: line.pgcc_account_id.account_id == pass_through
        )
        self.assertEqual(fee_line.dere12_vMovCred, 100000.0)
        self.assertEqual(fee_line.dere12_vApur, 100000.0)
        self.assertEqual(pass_line.dere12_vMovCred, 1150000.0)
        self.assertEqual(pass_line.dere12_vApur, 1150000.0)
        root = etree.fromstring(
            declaration.event_ids.filtered(
                lambda ev: ev.event_type == "D-1101"
            ).xml_content.encode("utf-8")
        )
        accounts = {
            node.findtext("{*}cCta"): node for node in root.findall(".//{*}infoConta")
        }
        self.assertEqual(
            accounts[fee_line.dere12_cCta].findtext("{*}vApur"), "100000.00"
        )
        self.assertEqual(accounts[fee_line.dere12_cCta].findtext("{*}natVApur"), "C")
        self.assertEqual(
            accounts[pass_line.dere12_cCta].findtext("{*}vApur"), "1150000.00"
        )
        self.assertEqual(accounts[pass_line.dere12_cCta].findtext("{*}natVApur"), "C")

    def test_d1101_variable_nature_uses_period_balance_side(self):
        variable = self.env["account.account"].create(
            {
                "name": "Variable nature receivable",
                "code": "DEREVAR1",
                "account_type": "asset_receivable",
                "reconcile": True,
                "company_ids": [Command.set(self.company.ids)],
                "l10n_br_dere_cta_interna": "91",
                "l10n_br_dere_dbr_mista": "000",
                "l10n_br_dere_cta_ref": "1",
                "l10n_br_dere_nat_cta": "V",
                "l10n_br_dere_cod_nat": "1",
                "l10n_br_dere_cod_trib": self.tax_equity.id,
            }
        )
        declaration = self._create_declaration("2027-11")
        declaration.action_generate_tables()
        self._accept_tables(declaration)
        self._post_entry("2027-11-10", variable, self.fee_account, 80.0)
        declaration.action_generate_d1101()
        line = declaration.trial_line_ids.filtered(
            lambda rec: rec.pgcc_account_id.account_id == variable
        )
        pgcc = line.pgcc_account_id
        self.assertEqual(pgcc.dere12_natCta, "V")
        self.assertEqual(line.dere12_natSaldoFinal, "D")
        self.assertEqual(line.dere12_natVApur, "D")
        self.assertEqual(line.dere12_vMovDebt, 80.0)
        self.assertEqual(line.dere12_vApur, 80.0)

    def test_d1199_requires_trial_and_forbids_deduction_flag(self):
        declaration = self._create_declaration()
        with self.assertRaises(UserError):
            declaration.action_generate_d1199()
        declaration.action_generate_tables()
        self._accept_tables(declaration)
        self._post_entry(
            "2026-10-20",
            self.receivable,
            self.fee_account,
            100.0,
        )
        declaration.action_generate_d1101()
        self.assertTrue(declaration.can_generate_trial)
        self.assertTrue(declaration.can_send_periodics)
        self.assertEqual(declaration.primary_action, "send_periodics")
        declaration.ind_inexist_dedu = True
        with self.assertRaises(UserError):
            declaration.action_generate_d1199()
        declaration.ind_inexist_dedu = False
        declaration.action_generate_d1199()
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1199")
        self.assertTrue(event.xml_content)
        self.assertEqual(declaration.state, "trial_ok")
        self.assertEqual(event.state, "generated")
        self.assertTrue(declaration.can_discard_local_closing)
        self.assertFalse(declaration.can_reopen_period)
        self.assertIn("<perApur>2026-10</perApur>", event.xml_content)
        self.assertNotIn("indInexistDedu", event.xml_content)
        self.assertRegex(event.event_id_attr, STRUCTURED_EVENT_ID_RE)
        self.assertTrue(event.event_id_attr.startswith("DeRE11991"))

    def test_d1101_pads_cnpj_root_in_event_id(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._post_entry(
            "2026-10-20",
            self.receivable,
            self.fee_account,
            100.0,
        )
        with patch.object(type(self.company), "_dere_cnpj", return_value="12345678"):
            declaration.action_generate_d1101()
        event = self._event(declaration, "D-1101")
        self.assertTrue(event.event_id_attr.startswith("DeRE11011"))
        self.assertIn("00000012345678", event.event_id_attr)

    def test_d1101_vapur_uses_adjustments_and_zero_keeps_opening_nature(self):
        declaration = self._create_declaration("2027-03")
        declaration.action_generate_tables()
        move = self._post_entry(
            "2027-03-10",
            self.receivable,
            self.fee_account,
            80.0,
            ref="Fee",
        )
        self._post_entry(
            "2027-02-28",
            self.receivable,
            self.equity_account,
            40.0,
            ref="Opening equity",
        )
        reversal = move._reverse_moves(
            default_values_list=[{"date": "2027-03-20", "ref": "Fee reversal"}]
        )
        if reversal.state != "posted":
            reversal.action_post()
        declaration.action_generate_d1101()
        fee_line = declaration.trial_line_ids.filtered(
            lambda line: line.pgcc_account_id.account_id == self.fee_account
        )
        equity_line = declaration.trial_line_ids.filtered(
            lambda line: line.pgcc_account_id.account_id == self.equity_account
        )
        self.assertEqual(fee_line.dere12_vMovCred, 80.0)
        self.assertEqual(fee_line.dere12_vMovDebt, 80.0)
        self.assertEqual(fee_line.dere12_vAjusteCred, 80.0)
        self.assertEqual(fee_line.dere12_vApur, 0.0)
        self.assertEqual(fee_line.dere12_natSaldoInic, "D")
        self.assertEqual(fee_line.dere12_natSaldoFinal, "D")
        self.assertEqual(equity_line.dere12_natSaldoInic, "C")
        self.assertEqual(equity_line.dere12_vSaldoFinal, 40.0)

    def test_d1101_result_opening_uses_closing_cycle(self):
        self.company.dere_freq_encerr = "A"
        declaration = self._create_declaration("2027-03")
        declaration.action_generate_tables()
        self._post_entry(
            "2026-12-15",
            self.receivable,
            self.fee_account,
            300.0,
            ref="Previous year",
        )
        self._post_entry(
            "2027-01-20",
            self.receivable,
            self.fee_account,
            50.0,
            ref="Current cycle",
        )
        declaration.action_generate_d1101()
        fee_line = declaration.trial_line_ids.filtered(
            lambda line: line.pgcc_account_id.account_id == self.fee_account
        )
        self.assertEqual(fee_line.dere12_vSaldoInic, 50.0)
        self.assertEqual(fee_line.dere12_natSaldoInic, "C")

    def test_d1106_must_match_trial_closing_balance(self):
        self.company.dere_subject_d1106 = True
        self._map_d1106_codtrib()
        self.equity_account.l10n_br_dere_reserve_invest = True
        self.env["l10n_br_dere.reserve.asset"].create(
            {
                "company_id": self.company.id,
                "id_ativo": "RES01",
                "desc_ativo": "Reserve",
                "account_id": self.equity_account.id,
            }
        )
        declaration = self._create_declaration("2027-04")
        declaration.action_generate_tables()
        self._post_entry(
            "2027-04-10",
            self.equity_account,
            self.fee_account,
            25.0,
            ref="Reserve buy",
        )
        declaration.action_generate_d1101()
        declaration.action_generate_d1106()
        declaration.reserve_line_ids.write({"dere12_vSaldoFinal": 1.0})
        with self.assertRaises(UserError):
            declaration.action_generate_d1199()
