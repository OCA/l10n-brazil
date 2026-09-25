# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.l10n_br_dere.models.dere_event_ops import DereEventParentMixin

from .common import DereCommon


@tagged("post_install", "-at_install")
class TestDereCoverageGaps(DereCommon):
    def test_mixin_defaults_and_operation_guards(self):
        declaration = self._prepare_trial("2028-01")
        mixin = DereEventParentMixin
        self.assertFalse(mixin._first_closing_accepted(declaration))
        self.assertFalse(mixin._can_create_next_event(declaration, "D-1199"))
        self.assertEqual(
            mixin._latest_event(declaration, "D-1101").event_type, "D-1101"
        )
        with self.assertRaises(UserError):
            declaration._assert_receipt_period("short", "2028-01")
        with self.assertRaises(UserError):
            declaration._prepare_oper_extra("D-1198", "2")
        with self.assertRaises(UserError):
            declaration._prepare_oper_extra("D-1101", "4")
        with self.assertRaises(UserError):
            declaration._prepare_oper_extra("D-1101", "3", {"motExcl": "1"})
        prepared = declaration._prepare_oper_extra(
            "D-1101", "1", {"nrRecibo": "drop-me"}
        )
        self.assertNotIn("nrRecibo", prepared)
        self.assertIsNone(declaration._assert_can_create_oper("D-1198", "2"))
        trial = self._event(declaration, "D-1101")
        trial.state = "sent"
        self.assertFalse(declaration._can_include_event("D-1101"))
        self.assertFalse(declaration._can_replace_or_exclude("D-1101"))
        with self.assertRaises(UserError):
            declaration._create_oper_event(
                "D-1101", tp_oper="2", parent_field="declaration_id"
            )
        trial.state = "generated"
        self.assertIsNone(declaration._assert_can_create_oper("D-1101", "2"))
        self._accept_event(declaration, "D-1101")
        self.assertEqual(declaration._default_periodic_tp_oper("D-1101"), "2")
        with self.assertRaises(UserError):
            declaration._assert_can_create_oper("D-1101", "1")
        with self.assertRaises(UserError):
            declaration._prepare_oper_extra("D-1106", "2")
        if declaration._has_d1106_codtrib():
            declaration.action_generate_d1106()
            self._accept_event(declaration, "D-1106")
        declaration.action_generate_d1199()
        self._accept_closing(declaration)
        self.assertFalse(declaration._can_replace_or_exclude("D-1101"))
        with self.assertRaises(UserError):
            declaration._assert_can_create_oper("D-1101", "2")
        self.company.dere_subject_d1121 = True
        declaration.invalidate_recordset()
        self.assertFalse(declaration._can_include_event("D-1121"))
        with self.assertRaises(UserError):
            declaration._assert_can_create_oper("D-1121", "1")
        with self.assertRaises(UserError):
            declaration._assert_can_create_oper("D-1121", "2")
        with self.assertRaises(UserError):
            declaration._assert_can_create_oper("D-1101", "4")
        declaration.action_mark_reopened()
        with self.assertRaises(UserError):
            declaration._assert_can_create_oper("D-1121", "4")

    def test_wizard_confirm_branches(self):
        declaration = self._prepare_trial("2028-02")
        line = self.env["l10n_br_dere.deduction.line"].create(
            {
                "declaration_id": declaration.id,
                "dere12_tpDFe": "03",
                "dere12_chDFe": self._nfe_access_key(3, "2028-02"),
                "dere12_dtEmi": "2028-02-01",
                "dere12_tpAtiv": "06",
                "dere12_vOper": 10.0,
                "dere12_vDedTotal": 10.0,
                "dere12_vDed": 10.0,
            }
        )
        wizard = self.env["l10n_br_dere.event.operation.wizard"].new(
            {"declaration_id": declaration.id, "event_type": "D-1121", "tp_oper": "4"}
        )
        wizard._onchange_declaration_id()
        self.assertEqual(wizard.deduction_line_ids._origin, line)
        period = self._table_period(declaration)
        exclude = self.env["l10n_br_dere.event.operation.wizard"].create(
            {
                "table_period_id": period.id,
                "event_type": "D-1001",
                "tp_oper": "3",
            }
        )
        with self.assertRaises(UserError):
            exclude.action_confirm()
        missing_start = exclude.copy(
            {"tp_oper": "2", "change_validity": True, "mot_excl": False}
        )
        with self.assertRaises(UserError):
            missing_start.action_confirm()
        fresh = self._create_declaration("2028-12")
        fresh.action_generate_tables()
        changed = self.env["l10n_br_dere.event.operation.wizard"].create(
            {
                "table_period_id": self._table_period(fresh).id,
                "event_type": "D-1001",
                "tp_oper": "2",
                "change_validity": True,
                "nova_ini_valid": "2028-03-01",
            }
        )
        self.assertEqual(
            changed.action_confirm()["type"], "ir.actions.act_window_close"
        )
        orphan = self.env["l10n_br_dere.event.operation.wizard"].create(
            {"event_type": "D-1101", "tp_oper": "2"}
        )
        with self.assertRaises(UserError):
            orphan.action_confirm()
        self._accept_event(declaration, "D-1101")
        replace = self.env["l10n_br_dere.event.operation.wizard"].create(
            {
                "declaration_id": declaration.id,
                "event_type": "D-1101",
                "tp_oper": "2",
            }
        )
        self.assertEqual(
            replace.action_confirm()["type"], "ir.actions.act_window_close"
        )
        unsupported = replace.copy({"event_type": "D-1199", "tp_oper": "2"})
        with self.assertRaises(UserError):
            unsupported.action_confirm()

    def test_declaration_helpers_and_wrappers(self):
        declaration = self._create_declaration("2028-03")
        declaration.table_period_id = False
        self.assertFalse(declaration._event_records("D-1001"))
        bare = self.env["l10n_br_dere.declaration"].new({"company_id": self.company.id})
        with self.assertRaises(UserError):
            bare._require_table_period()
        with patch.object(
            type(declaration.company_id), "_dere_cnpj_root", lambda self: "123"
        ):
            with self.assertRaises(UserError):
                declaration._header_vals(event_type="D-1101")
        self.assertEqual(declaration._activity_codes("31"), ["02A"])
        self.assertEqual(
            declaration._account_name_for_xml(self.env["account.account"]), ""
        )
        group = declaration._pgcc_row_from_group(self.parent_group, set())
        self.assertTrue(group is None or isinstance(group, dict))
        declaration.action_generate_tables()
        self._accept_tables(declaration)
        pgcc_account = declaration.pgcc_account_ids.filtered("account_id")[
            :1
        ].account_id
        anchor = self._post_entry(
            "2028-03-09", self.receivable, pgcc_account, 10.0, ref="anchor"
        )
        credited = self._post_entry(
            "2028-03-10", self.receivable, pgcc_account, 25.0, ref="gap"
        )
        credited.button_draft()
        credited.reversed_entry_id = anchor
        credited.action_post()
        _opening, _cycle, period, _prev, _start = declaration._account_balances()
        self.assertGreater(period[pgcc_account.id]["ajuste_debt"], 0.0)
        declaration.action_generate_d1101()
        pgcc = declaration.pgcc_account_ids.filtered(
            lambda line: line.dere12_codNat not in ("4", "5")
        )[:1]
        opening = {pgcc.account_id.id: 7.0}
        self.assertEqual(
            declaration._trial_opening(pgcc, opening, {}, {}, 3, set()), 7.0
        )
        self.assertFalse(
            declaration._needs_trial_after_reopening(self.env["l10n_br_dere.event"])
        )
        self.assertFalse(declaration._can_create_next_event("D-1101"))
        self.assertEqual(
            declaration.action_exclude_d1101()["res_model"],
            "l10n_br_dere.event.operation.wizard",
        )
        self.assertEqual(
            declaration.action_exclude_d1106()["res_model"],
            "l10n_br_dere.event.operation.wizard",
        )
        self.assertEqual(
            declaration.action_exclude_d1121()["res_model"],
            "l10n_br_dere.event.operation.wizard",
        )
        self.assertEqual(
            declaration.action_rectify_d1121()["res_model"],
            "l10n_br_dere.event.operation.wizard",
        )
        action = declaration.action_replace_tables()
        self.assertEqual(action["res_model"], "l10n_br_dere.event.operation.wizard")
        self.assertEqual(
            declaration.action_exclude_tables()["res_model"],
            "l10n_br_dere.event.operation.wizard",
        )
        with patch.object(
            type(declaration.table_period_id),
            "action_send_tables",
            lambda self: {"type": "ir.actions.client"},
        ):
            self.assertEqual(
                declaration.action_send_tables()["type"], "ir.actions.client"
            )
        with patch.object(
            type(declaration),
            "_send_events",
            lambda self, events: {"type": "ir.actions.client"},
        ):
            self.assertEqual(
                declaration.action_send_periodics()["type"], "ir.actions.client"
            )
        company = declaration.company_id
        certificate = company.certificate_nfe_id
        ecnpj = company.certificate_ecnpj_id
        company.write({"certificate_nfe_id": False, "certificate_ecnpj_id": False})
        with self.assertRaises(UserError):
            declaration._get_dere_certificate()
        company.write(
            {"certificate_nfe_id": certificate.id, "certificate_ecnpj_id": ecnpj.id}
        )

    def test_d1106_exclusion_and_reserve_sync_without_snapshot(self):
        declaration = self._prepare_d1106_trial("2028-04")
        empty = declaration.copy({"per_apur": "2028-05"})
        empty.pgcc_account_ids = False
        self.assertTrue(empty._sync_reserve_lines_from_assets())
        self._accept_event(declaration, "D-1101")
        declaration.action_generate_d1106()
        self._accept_event(declaration, "D-1106")
        excluded = declaration._generate_d1106(tp_oper="3", extra={"motExcl": "9"})
        self.assertEqual(excluded.tp_oper, "3")
        self.assertEqual(excluded.mot_excl, "9")
        declaration.action_replace_d1106()
        replaced = self._event(declaration, "D-1106")
        self.assertEqual(replaced.tp_oper, "2")

    def test_d1121_exclusion_and_rectification_items(self):
        self.company.dere_subject_d1121 = True
        declaration = self._prepare_trial("2028-06")
        key = self._nfe_access_key(4, "2028-06")
        line = self.env["l10n_br_dere.deduction.line"].create(
            {
                "declaration_id": declaration.id,
                "dere12_tpDFe": "03",
                "dere12_chDFe": key,
                "dere12_dtEmi": "2028-06-02",
                "dere12_tpAtiv": "06",
                "dere12_vOper": 50.0,
                "dere12_vDedTotal": 20.0,
                "dere12_vDed": 20.0,
            }
        )
        with self.assertRaises(UserError):
            declaration._ensure_deduction_items(line)
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "partner_id": (
                    self.env.ref(
                        "l10n_br_base.res_partner_cliente1_sp",
                        raise_if_not_found=False,
                    )
                    or self.env["res.partner"].create({"name": "DeRE gap customer"})
                ).id,
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_compras").id,
                "document_date": "2028-06-02 12:00:00",
                "document_key": key,
                "issuer": "partner",
                "state_edoc": "a_enviar",
            }
        )
        line.document_id = document
        with self.assertRaises(UserError):
            declaration._ensure_deduction_items(line)
        fiscal_line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "name": "Item",
                "quantity": 1.0,
                "price_unit": 20.0,
                "fiscal_amount_total": 20.0,
            }
        )
        if "nfe40_nItem" in fiscal_line._fields:
            fiscal_line.nfe40_nItem = "7"
        declaration._ensure_deduction_items(line)
        self.assertEqual(
            line.item_ids.dere12_nItem,
            "7" if "nfe40_nItem" in fiscal_line._fields else "1",
        )
        declaration.ind_inexist_dedu = False
        declaration.action_generate_d1121()
        self._accept_event(declaration, "D-1121")
        declaration.action_replace_d1121()
        self.assertEqual(self._event(declaration, "D-1121").tp_oper, "2")
        excluded = declaration._generate_d1121(tp_oper="3", extra={"motExcl": "2"})
        self.assertEqual(excluded.mot_excl, "2")
        excluded.write(
            {
                "state": "accepted",
                "nr_recibo": self._event_receipt("D-1121", "2028-06"),
                "cd_retorno": "1",
            }
        )
        if declaration._has_d1106_codtrib():
            declaration.action_generate_d1106()
            self._accept_event(declaration, "D-1106")
        declaration.action_generate_d1199()
        self._accept_closing(declaration)
        declaration.action_mark_reopened()
        self._accept_reopening(declaration)
        with self.assertRaises(UserError):
            declaration._generate_d1121(tp_oper="4", extra={})
        rectified = declaration._generate_d1121(
            tp_oper="4", extra={"finEvt": "2"}, lines=line
        )
        self.assertIn("<chDFeRetif>", rectified.xml_content)
        self.assertTrue(declaration._needs_trial_after_reopening(False))
        with self.assertRaises(UserError):
            declaration._assert_d1199_prerequisites()

    def test_closing_flags_and_send_order(self):
        declaration = self._prepare_trial("2028-07")
        declaration.ind_inexist_dedu = True
        with self.assertRaises(UserError):
            declaration._d1199_info_vals()
        self.company.dere_subject_d1121 = True
        declaration.invalidate_recordset()
        declaration.ind_inexist_dedu = True
        self.assertEqual(declaration._d1199_info_vals()["indInexistDedu"], "1")
        trial = self._event(declaration, "D-1101")
        trial.write(
            {
                "nr_recibo_prev": "1011-202807-" + "9" * 19,
                "nr_recibo": self._event_receipt("D-1101", "2028-07"),
            }
        )
        with self.assertRaises(UserError):
            declaration._assert_pgcc_receipt_matches_trial()
        with self.assertRaises(UserError):
            declaration._assert_send_order(["D-1101", "D-1106"])
        with self.assertRaises(UserError):
            declaration._assert_send_order(["D-1001", "D-1101"])
        sent = self._event(declaration, "D-1199")
        if not sent:
            declaration.env["l10n_br_dere.event"].create(
                {
                    "declaration_id": declaration.id,
                    "event_type": "D-1198",
                    "tp_oper": "1",
                    "state": "sent",
                    "tp_amb": "2",
                    "ver_aplic": "1",
                }
            )
        self.assertFalse(declaration._can_include_event("D-1198"))
        self.assertFalse(declaration._extract_protocol(""))
        self.assertEqual(declaration._extract_protocol("1.234567.89"), "1.234567.89")
        self.assertFalse(declaration._extract_protocol("{"))
        self.assertFalse(declaration._extract_protocol('{"other": 1}'))
        self.assertFalse(declaration._extract_protocol("not-a-protocol"))
        self.assertFalse(declaration._extract_protocol("<not-xml"))

    def test_table_period_edges_and_consult(self):
        Table = self.env["l10n_br_dere.table.period"]
        self.assertFalse(Table._find_covering(False, "2028-08-01"))
        created = Table._get_or_create_for(
            self.company, fields.Date.to_date("2000-01-15")
        )
        self.assertEqual(str(created.ini_valid), "2000-01-01")
        with self.assertRaises(ValidationError):
            created.write({"fim_valid": "1999-12-01"})
        declaration = self._create_declaration("2028-08")
        period = self._table_period(declaration)
        period.action_generate_d1001()
        period.action_generate_d1011()
        with patch.object(type(period), "_generate_d1001", lambda self, **kwargs: True):
            with patch.object(
                type(period), "_generate_d1011", lambda self, **kwargs: True
            ):
                draft = period.copy({"ini_valid": "2001-01-01", "state": "draft"})
                draft.action_generate_tables()
                self.assertEqual(draft.state, "generated")
        self.assertEqual(
            period.action_replace_tables()["res_model"],
            "l10n_br_dere.event.operation.wizard",
        )
        self.assertEqual(
            period.action_exclude_tables()["res_model"],
            "l10n_br_dere.event.operation.wizard",
        )
        with self.assertRaises(UserError):
            period._assert_send_order(["D-1001", "D-1011"])
        d1001 = self._event(declaration, "D-1001")
        d1001.state = "generated"
        with self.assertRaises(UserError):
            period._assert_send_order(["D-1011"])
        with patch.object(
            type(period),
            "_send_events",
            lambda self, events: {"type": "ir.actions.client"},
        ):
            self.assertEqual(period.action_send_tables()["type"], "ir.actions.client")
        with patch.object(type(period.company_id), "_dere_cnpj_root", lambda self: ""):
            with self.assertRaises(UserError):
                period._header_vals(event_type="D-1001")
        with self.assertRaises(UserError):
            period.action_consult_results()
        batch = self.env["l10n_br_dere.batch"].create(
            {
                "name": "done",
                "table_period_id": period.id,
                "tp_amb": "2",
                "protocol": "1.000001.1",
                "state": "done",
            }
        )
        notice = period.action_consult_results()
        self.assertEqual(notice["tag"], "display_notification")
        self.assertFalse(period._apply_nova_validade(d1001.browse()))
        d1001.xml_content = "<e/>"
        self.assertFalse(period._apply_nova_validade(d1001))
        d1001.xml_content = (
            "<e><novaValidade><iniValid>2028-09-01</iniValid></novaValidade></e>"
        )
        period._apply_nova_validade(d1001)
        self.assertEqual(str(period.ini_valid), "2028-09-01")
        self.assertFalse(period.fim_valid)
        self.assertFalse(period._extract_protocol(""))
        self.assertEqual(period._extract_protocol("2.000001.12"), "2.000001.12")
        self.assertFalse(period._extract_protocol("{"))
        self.assertEqual(
            period._extract_protocol('{"protocolo": "2.000001.13"}'), "2.000001.13"
        )
        self.assertFalse(period._extract_protocol("plain"))
        self.assertFalse(period._extract_protocol("<not-xml"))
        self.assertFalse(period._apply_consult_result(batch, ""))
        self.assertFalse(period._apply_consult_result(batch, "<not-xml"))
        self.assertFalse(
            period._apply_consult_result(
                batch, "<retorno><cdResposta>1</cdResposta></retorno>"
            )
        )
        event = self._event(declaration, "D-1011")
        event.state = "sent"
        batch.event_ids = event
        self.assertFalse(
            period._apply_consult_result(
                batch,
                "<retorno><cdResposta>4</cdResposta>"
                "<ocorrencias><codigo>9</codigo><descricao>x</descricao>"
                "</ocorrencias></retorno>",
            )
        )
        self.assertEqual(event.state, "rejected")
        self.assertTrue(event.occurrence_ids)
