# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_dere.constants import STRUCTURED_EVENT_ID_RE

from .common import DereCommon


@tagged("post_install", "-at_install")
class TestDereAuxiliaryEvents(DereCommon):
    def _prepare_trial(self, period="2026-11"):
        declaration = self._create_declaration(period)
        declaration.action_generate_tables()
        self._accept_tables(declaration)
        self._post_entry(
            f"{period}-10",
            self.receivable,
            self.fee_account,
            100.0,
        )
        declaration.action_generate_d1101()
        return declaration

    def test_primary_action_follows_d1106_when_company_is_subject(self):
        self.company.dere_subject_d1106 = True
        declaration = self._prepare_trial()
        self.assertEqual(declaration.primary_action, "send_periodics")
        declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1101").write(
            {
                "state": "accepted",
                "nr_recibo": "1101-202611-0000000000000000001",
                "cd_retorno": "1",
            }
        )
        self.assertTrue(declaration.can_generate_d1106)
        self.assertFalse(declaration.can_close_period)
        self.assertEqual(declaration.primary_action, "generate_d1106")
        declaration.action_generate_d1106()
        self.assertEqual(declaration.primary_action, "send_periodics")

    def test_d1106_sem_aplic_when_subject_without_assets(self):
        self.company.dere_subject_d1106 = True
        declaration = self._prepare_trial()
        declaration.action_generate_d1106()
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1106")
        self.assertTrue(event.xml_content)
        self.assertIn("<semAplic>1</semAplic>", event.xml_content)
        self.assertRegex(event.event_id_attr, STRUCTURED_EVENT_ID_RE)
        self.assertTrue(event.event_id_attr.startswith("DeRE11062"))

    def test_d1106_with_asset_formulas(self):
        self.company.dere_subject_d1106 = True
        self.equity_account.l10n_br_dere_reserve_invest = True
        self.env["l10n_br_dere.reserve.asset"].create(
            {
                "company_id": self.company.id,
                "id_ativo": "CDB2026001",
                "desc_ativo": "Bank certificate",
                "account_id": self.equity_account.id,
            }
        )
        declaration = self._prepare_trial()
        declaration.action_generate_d1106()
        line = declaration.reserve_line_ids
        self.assertEqual(line.dere12_idAtivo, "CDB2026001")
        line.write(
            {
                "dere12_vSaldoInic": 1000.0,
                "dere12_vRendPerReceb": 10.0,
                "dere12_vVarMensal": 5.0,
                "dere12_vPrincLiqResg": 20.0,
                "dere12_vRendLiqResg": 2.0,
            }
        )
        declaration.with_context(dere_skip_reserve_gl=True).action_generate_d1106()
        self.assertEqual(line.dere12_vSaldoFinal, 985.0)
        self.assertEqual(line.dere12_vApur, 12.0)
        root = etree.fromstring(
            declaration.event_ids.filtered(
                lambda ev: ev.event_type == "D-1106"
            ).xml_content.encode("utf-8")
        )
        self.assertEqual(root.findtext(".//{*}cCta"), line.dere12_cCta)
        self.assertEqual(root.find(".//{*}detAtivo").get("idAtivo"), "CDB2026001")
        self.assertEqual(root.findtext(".//{*}vSaldoFinal"), "985.00")
        self.assertEqual(root.findtext(".//{*}vApur"), "12.00")
        self.assertIsNone(root.find(".//{*}semAplic"))

    def _create_reserve_asset(self, account, id_ativo="CDB2026001"):
        account.l10n_br_dere_reserve_invest = True
        return self.env["l10n_br_dere.reserve.asset"].create(
            {
                "company_id": self.company.id,
                "id_ativo": id_ativo,
                "desc_ativo": "Bank certificate",
                "account_id": account.id,
            }
        )

    def test_d1106_fills_from_gl_one_asset(self):
        self.company.dere_subject_d1106 = True
        self._create_reserve_asset(self.equity_account)
        self._post_entry("2026-10-31", self.equity_account, self.receivable, 1000.0)
        self._post_entry("2026-11-12", self.equity_account, self.fee_account, 10.0)
        declaration = self._prepare_trial()
        declaration.action_generate_d1106()
        line = declaration.reserve_line_ids
        self.assertEqual(line.dere12_vSaldoInic, 1000.0)
        self.assertEqual(line.dere12_vVarMensal, 10.0)
        self.assertEqual(line.dere12_vRendPerReceb, 10.0)
        self.assertEqual(line.dere12_vPrincLiqResg, 0.0)
        self.assertEqual(line.dere12_vApur, 10.0)
        self.assertEqual(line.dere12_vSaldoFinal, 1010.0)

    def test_d1106_fills_redemption_income_from_same_move(self):
        self.company.dere_subject_d1106 = True
        self._create_reserve_asset(self.equity_account)
        self._post_entry("2026-10-31", self.equity_account, self.receivable, 100.0)
        self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": "2026-11-20",
                "journal_id": self.journal.id,
                "company_id": self.company.id,
                "ref": "DeRE reserve redemption",
                "line_ids": [
                    Command.create(
                        {
                            "account_id": self.receivable.id,
                            "name": "Redemption",
                            "debit": 22.0,
                            "credit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": self.equity_account.id,
                            "name": "Principal",
                            "debit": 0.0,
                            "credit": 20.0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": self.fee_account.id,
                            "name": "Gain",
                            "debit": 0.0,
                            "credit": 2.0,
                        }
                    ),
                ],
            }
        ).action_post()
        declaration = self._prepare_trial()
        declaration.action_generate_d1106()
        line = declaration.reserve_line_ids
        self.assertEqual(line.dere12_vPrincLiqResg, 20.0)
        self.assertEqual(line.dere12_vRendLiqResg, 2.0)
        self.assertEqual(line.dere12_vApur, 2.0)
        self.assertEqual(line.dere12_vSaldoFinal, 80.0)

    def test_d1106_fills_mapped_income_account(self):
        self.company.dere_subject_d1106 = True
        income = self.env["account.account"].create(
            {
                "name": "Reserve coupon income",
                "code": "DEREINC",
                "account_type": "income",
                "company_ids": [Command.set(self.company.ids)],
            }
        )
        self.equity_account.l10n_br_dere_reserve_income_account_id = income.id
        self._create_reserve_asset(self.equity_account)
        self._post_entry("2026-11-18", self.receivable, income, 15.0)
        declaration = self._prepare_trial()
        declaration.action_generate_d1106()
        line = declaration.reserve_line_ids
        self.assertEqual(line.dere12_vRendPerReceb, 15.0)
        self.assertEqual(line.dere12_vVarMensal, 0.0)
        self.assertEqual(line.dere12_vApur, 15.0)

    def test_d1106_skips_gl_when_two_assets_share_account(self):
        self.company.dere_subject_d1106 = True
        self._create_reserve_asset(self.equity_account, "CDB2026001")
        self._create_reserve_asset(self.equity_account, "CDB2026002")
        self._post_entry("2026-11-12", self.equity_account, self.fee_account, 50.0)
        declaration = self._prepare_trial()
        declaration.action_generate_d1106()
        self.assertEqual(
            declaration.reserve_line_ids.mapped("dere12_vVarMensal"), [0.0, 0.0]
        )
        self.assertEqual(
            declaration.reserve_line_ids.mapped("dere12_vRendPerReceb"), [0.0, 0.0]
        )

    def test_close_requires_d1106_when_subject(self):
        self.company.dere_subject_d1106 = True
        declaration = self._prepare_trial()
        with self.assertRaises(UserError):
            declaration.action_generate_d1199()
        declaration.action_generate_d1106()
        declaration.action_generate_d1199()
        self.assertEqual(declaration.state, "trial_ok")
        self.assertTrue(declaration.can_discard_local_closing)
        self.assertFalse(declaration.can_reopen_period)

    def test_d1121_from_inbound_fiscal_document(self):
        self.company.dere_subject_d1121 = True
        operation = self.env.ref("l10n_br_fiscal.fo_compras")
        operation.write(
            {
                "l10n_br_dere_deductible": True,
                "l10n_br_dere_tp_ativ": "06",
            }
        )
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "partner_id": self.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                "fiscal_operation_id": operation.id,
                "document_date": "2026-11-15 12:00:00",
                "document_key": self._nfe_access_key(),
                "issuer": "partner",
                "state_edoc": "a_enviar",
            }
        )
        declaration = self._prepare_trial()
        declaration.action_load_deductions()
        line = declaration.deduction_line_ids
        self.assertEqual(line.document_id, document)
        self.assertEqual(line.dere12_tpDFe, "03")
        self.assertEqual(line.dere12_tpAtiv, "06")
        line.write(
            {
                "dere12_vOper": 800.0,
                "dere12_vDedTotal": 800.0,
                "dere12_vDed": 800.0,
            }
        )
        declaration.action_generate_d1121()
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1121")
        root = etree.fromstring(event.xml_content.encode("utf-8"))
        self.assertEqual(root.findtext(".//{*}tpDFe"), "03")
        self.assertEqual(root.findtext(".//{*}tpAtiv"), "06")
        self.assertEqual(root.findtext(".//{*}chDFe"), document.document_key)
        self.assertEqual(root.findtext(".//{*}vOper"), "800.00")
        self.assertIsNone(root.find(".//{*}itemDFe"))
        self.assertRegex(event.event_id_attr, STRUCTURED_EVENT_ID_RE)
        self.assertTrue(event.event_id_attr.startswith("DeRE11212"))

    def test_load_deductions_without_documents_reports_absence(self):
        self.company.dere_subject_d1121 = True
        declaration = self._prepare_trial()
        self._accept_event(declaration, "D-1101")
        self.assertEqual(declaration.primary_action, "load_deductions")
        action = declaration.action_load_deductions()
        self.assertEqual(action["tag"], "display_notification")
        self.assertFalse(declaration.deduction_line_ids)
        self.assertTrue(declaration.ind_inexist_dedu)
        self.assertTrue(declaration.can_close_period)
        self.assertEqual(declaration.primary_action, "close_period")

    def test_closing_waits_for_the_deduction_load(self):
        self.company.dere_subject_d1121 = True
        declaration = self._prepare_trial()
        self._accept_event(declaration, "D-1101")
        self.assertFalse(declaration.can_close_period)
        declaration.action_load_deductions()
        self.assertTrue(declaration.can_close_period)

    def test_d1199_auto_ind_inexist_dedu_without_documents(self):
        self.company.dere_subject_d1106 = False
        self.company.dere_subject_d1121 = True
        declaration = self._prepare_trial()
        declaration.action_generate_d1199()
        self.assertTrue(declaration.ind_inexist_dedu)
        xml = declaration.event_ids.filtered(
            lambda ev: ev.event_type == "D-1199"
        ).xml_content
        self.assertIn("<indInexistDedu>1</indInexistDedu>", xml)
        self.assertFalse(
            declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1121")
        )

    def test_ind_inexist_dedu_conflicts_with_deduction_lines(self):
        self.company.dere_subject_d1121 = True
        declaration = self._prepare_trial()
        self.env["l10n_br_dere.deduction.line"].create(
            {
                "declaration_id": declaration.id,
                "dere12_tpDFe": "03",
                "dere12_chDFe": self._nfe_access_key(2),
                "dere12_dtEmi": "2026-11-01",
                "dere12_tpAtiv": "06",
                "dere12_vOper": 50.0,
                "dere12_vDedTotal": 50.0,
                "dere12_vDed": 50.0,
            }
        )
        declaration.ind_inexist_dedu = True
        with self.assertRaises(UserError):
            declaration.action_generate_d1121()
        with self.assertRaises(UserError):
            declaration.action_generate_d1199()

    def test_send_order_requires_receipts(self):
        self.company.dere_subject_d1106 = True
        declaration = self._prepare_trial()
        declaration.action_generate_d1106()
        d1106 = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1106")
        with self.assertRaises(UserError):
            declaration._send_events(d1106)
        self._accept_event(declaration, "D-1101")
        declaration._assert_send_order(["D-1106"])
        declaration.action_generate_d1199()
        d1199 = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1199")
        with self.assertRaises(UserError):
            declaration._send_events(d1199)
        self._accept_event(declaration, "D-1106")
        declaration._assert_send_order(["D-1199"])
