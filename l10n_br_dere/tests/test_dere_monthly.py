# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

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
        self.assertEqual(fee_line.v_mov_cred, 1000.0)
        self.assertEqual(fee_line.v_apur, 1000.0)
        self.assertEqual(equity_line.v_saldo_inic, 250.0)
        self.assertEqual(equity_line.v_mov_debt, 0.0)
        self.assertEqual(equity_line.v_mov_cred, 0.0)
        self.assertEqual(equity_line.v_apur, 0.0)
        root = etree.fromstring(
            declaration.event_ids.filtered(
                lambda ev: ev.event_type == "D-1101"
            ).xml_content.encode("utf-8")
        )
        self.assertEqual(root.findtext(".//{*}perApur"), "2026-10")
        self.assertEqual(len(root.find(".//{*}evtBalancete").get("id") or ""), 42)

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
                "l10n_br_dere_ind_cta": "A",
                "l10n_br_dere_nat_cta": "C",
                "l10n_br_dere_cod_nat": "4",
                "l10n_br_dere_cod_trib": self.tax_admin_fee.id,
                "l10n_br_dere_nivel_cta": 1,
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
                "l10n_br_dere_ind_cta": "A",
                "l10n_br_dere_nat_cta": "C",
                "l10n_br_dere_cod_nat": "2",
                "l10n_br_dere_nivel_cta": 1,
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
        self.assertEqual(fee_line.v_mov_cred, 100000.0)
        self.assertEqual(fee_line.v_apur, 100000.0)
        self.assertEqual(pass_line.v_mov_cred, 1150000.0)
        self.assertEqual(pass_line.v_apur, 0.0)
        root = etree.fromstring(
            declaration.event_ids.filtered(
                lambda ev: ev.event_type == "D-1101"
            ).xml_content.encode("utf-8")
        )
        accounts = {
            node.findtext("{*}cCta"): node for node in root.findall(".//{*}infoConta")
        }
        self.assertEqual(accounts[fee_line.c_cta].findtext("{*}vApur"), "100000.00")
        self.assertEqual(accounts[fee_line.c_cta].findtext("{*}natVApur"), "C")
        self.assertEqual(accounts[pass_line.c_cta].findtext("{*}vApur"), "0.00")
        self.assertIsNone(accounts[pass_line.c_cta].find("{*}natVApur"))

    def test_d1199_requires_trial_and_forbids_deduction_flag(self):
        declaration = self._create_declaration()
        with self.assertRaises(UserError):
            declaration.action_generate_d1199()
        declaration.action_generate_tables()
        self._post_entry(
            "2026-10-20",
            self.receivable,
            self.fee_account,
            100.0,
        )
        declaration.action_generate_d1101()
        declaration.ind_inexist_dedu = True
        with self.assertRaises(UserError):
            declaration.action_generate_d1199()
        declaration.ind_inexist_dedu = False
        declaration.action_generate_d1199()
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1199")
        self.assertTrue(event.xml_content)
        self.assertEqual(declaration.state, "closed")
        self.assertIn("<perApur>2026-10</perApur>", event.xml_content)
        self.assertNotIn("indInexistDedu", event.xml_content)
