# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.l10n_br_dere.models import xml_builder
from odoo.addons.l10n_br_dere_spec.models import xsd_validator

from .common import DereCommon

RETURN_OCCURRENCE = """<?xml version="1.0" encoding="utf-8"?>
<DeRE xmlns="http://www.dere.gov.br/schemas/evtRetornoTabela/v1_0_1">
  <evtRetornoTabela>
    <ideStatus>
      <cdRetorno>0</cdRetorno>
      <descRetorno>Erro</descRetorno>
    </ideStatus>
    <ocorrencias>
      <codigo>12</codigo>
      <descricao>Invalid activity</descricao>
      <tipo>1</tipo>
      <localizacao>plAssistSaude</localizacao>
    </ocorrencias>
  </evtRetornoTabela>
</DeRE>
"""

REJECTED_LOTE = """<?xml version="1.0" encoding="utf-8"?>
<DeRE xmlns="http://www.dere.gov.br/schemas/retornoLoteDere/v1_0_1">
  <retornoLoteEventos>
    <status>
      <cdResposta>4</cdResposta>
      <descResposta>Rejected</descResposta>
    </status>
  </retornoLoteEventos>
</DeRE>
"""


@tagged("post_install", "-at_install")
class TestDereCoverage(DereCommon):
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

    def _deduction_vals(self, declaration, **extra):
        vals = {
            "declaration_id": declaration.id,
            "dere12_tpDFe": "03",
            "dere12_chDFe": self._nfe_access_key(9),
            "dere12_dtEmi": f"{declaration.per_apur}-01",
            "dere12_tpAtiv": "06",
            "dere12_vOper": 100.0,
            "dere12_vDedTotal": 100.0,
            "dere12_vDed": 100.0,
        }
        vals.update(extra)
        return vals

    def test_guards_block_auxiliary_events_out_of_order(self):
        declaration = self._create_declaration("2025-01")
        with self.assertRaises(UserError):
            declaration.action_generate_d1106()
        with self.assertRaises(UserError):
            declaration.action_load_deductions()
        with self.assertRaises(UserError):
            declaration.action_generate_d1121()
        self.company.dere_subject_d1106 = True
        with self.assertRaises(UserError):
            declaration.action_generate_d1106()
        self.company.dere_subject_d1121 = True
        with self.assertRaises(UserError):
            declaration.action_load_deductions()
        declaration = self._prepare_trial("2025-02")
        with self.assertRaises(UserError):
            declaration.action_generate_d1121()
        self.assertFalse(declaration._event_needs_new_generation("D-1101"))

    def test_d1001_secondary_regimes_export_financial_and_prize_blocks(self):
        financial = self.env.ref("l10n_br_dere.activity_21_01a")
        prize = self.env.ref("l10n_br_dere.activity_41_01a")
        self.company.write(
            {
                "dere_reg_trib_secund": "1",
                "dere_activity_ids": [
                    Command.set((self.activity_admin | financial | prize).ids)
                ],
            }
        )
        declaration = self._create_declaration("2025-03")
        declaration.action_generate_d1001()
        xml = self._event(declaration, "D-1001").xml_content
        self.assertIn("<servFinanc>", xml)
        self.assertIn("<plAssistSaude>", xml)
        self.company.dere_reg_trib_princ = "3"
        self.company.dere_reg_trib_secund = False
        self.company.dere_activity_ids = [Command.set(prize.ids)]
        prize_declaration = self._create_declaration("2025-04")
        prize_declaration.action_generate_d1001()
        prize_xml = self._event(prize_declaration, "D-1001").xml_content
        self.assertIn("<prognosticos>", prize_xml)
        self.assertNotIn("<plAssistSaude>", prize_xml)

    def test_xml_builder_covers_optional_nodes_and_empty_payloads(self):
        header = {
            "id": "A" + "0" * 41,
            "tpOper": "1",
            "tpAmb": "2",
            "verAplic": "test",
            "nrInsc": "12345678",
            "iniValid": "2026-01-01",
            "perApur": "2026-01",
            "regTribPrinc": "3",
            "regTribSecund": ["1"],
            "indNatTrib": "0",
            "tpAtividadeFinanc": ["01A"],
            "tpAtividadeProg": ["01A"],
            "UFCredenc": ["SP"],
        }
        d1001 = xml_builder.build_d1001(header)
        self.assertIn("<servFinanc>", d1001)
        self.assertIn("<UFCredenc>SP</UFCredenc>", d1001)
        d1101 = xml_builder.build_d1101(
            header,
            [
                {
                    "cCta": "311",
                    "natSaldoInic": "C",
                    "vSaldoInic": 0,
                    "vMovDebt": 0,
                    "vAjusteDebt": 1.5,
                    "vMovCred": 10,
                    "vAjusteCred": 0.5,
                    "natSaldoFinal": "C",
                    "vSaldoFinal": 12,
                    "vApur": 10,
                    "natVApur": "C",
                }
            ],
        )
        self.assertIn("<vAjusteDebt>1.50</vAjusteDebt>", d1101)
        self.assertIn("<vAjusteCred>0.50</vAjusteCred>", d1101)
        with self.assertRaises(ValueError):
            xml_builder.build_d1106(header, [])
        with self.assertRaises(ValueError):
            xml_builder.build_d1121(header, [])
        items_xml = xml_builder.build_d1121(
            header,
            [
                {
                    "tpDFe": "03",
                    "chDFe": self._nfe_access_key(3),
                    "dtEmi": "2026-01-01",
                    "tpAtiv": "06",
                    "vOper": 100,
                    "vDedTotal": 80,
                    "vDed": 80,
                    "items": [
                        {
                            "nItem": "1",
                            "vItem": 100,
                            "vItemDedTotal": 80,
                            "vItemDed": 80,
                        }
                    ],
                }
            ],
        )
        self.assertIn("<itemDFe>", items_xml)
        self.assertIn("<nItem>1</nItem>", items_xml)
        parsed = xml_builder.parse_return(RETURN_OCCURRENCE)
        self.assertEqual(parsed["ocorrencias"][0]["codigo"], "12")
        parsed_bytes = xml_builder.parse_return(RETURN_OCCURRENCE.encode())
        self.assertEqual(parsed_bytes["cdRetorno"], "0")
        d1106 = xml_builder.build_d1106(
            {**header, "semAplic": False},
            [
                {
                    "cCta": "21",
                    "idAtivo": "CDB1",
                    "descAtivo": "CDB",
                    "vSaldoInic": 10,
                    "vRendPerReceb": 1.1,
                    "vVarMensal": -2.5,
                    "vPrincLiqResg": 0,
                    "vRendLiqResg": 0.4,
                    "vSaldoFinal": 7.5,
                    "vApur": 1.5,
                }
            ],
        )
        self.assertIn("<vVarMensal>-2.50</vVarMensal>", d1106)
        self.assertIn("<vRendPerReceb>1.10</vRendPerReceb>", d1106)
        self.assertIn("<vRendLiqResg>0.40</vRendLiqResg>", d1106)
        d1198 = xml_builder.build_d1198(
            {**header, "nrReciboReab": "1199-202601-" + "0" * 19}
        )
        self.assertIn("<nrReciboReab>", d1198)
        d1199 = xml_builder.build_d1199({**header, "indInexistDedu": "1"})
        self.assertIn("<indInexistDedu>1</indInexistDedu>", d1199)
        lote = xml_builder.build_lote("12345678", [{"id": header["id"], "xml": d1001}])
        self.assertIn("<loteEventos>", lote)
        with self.assertRaises(ValueError):
            xml_builder.build_d1001({**header, "tpOper": False})
        self.assertEqual(xml_builder._money(0.001), "0.00")
        self.assertEqual(xml_builder._money(-3.2), "3.20")

    def test_trial_syncs_pgcc_and_skips_duplicate_account_codes(self):
        duplicate = self.env["account.account"].create(
            {
                "name": "Duplicate DeRE mapping",
                "code": "DEREDUP",
                "account_type": "income",
                "company_ids": [Command.set(self.company.ids)],
                "l10n_br_dere_cta_interna": self.fee_account.l10n_br_dere_cta_interna,
                "l10n_br_dere_dbr_mista": "000",
                "l10n_br_dere_cta_ref": "120110006",
                "l10n_br_dere_nat_cta": "C",
                "l10n_br_dere_cod_nat": "4",
                "l10n_br_dere_cod_trib": self.tax_admin_fee.id,
            }
        )
        self.assertTrue(duplicate.l10n_br_dere_cta)
        declaration = self._create_declaration("2025-05")
        self._post_entry("2025-05-10", self.receivable, self.fee_account, 20.0)
        declaration.action_generate_d1101()
        codes = declaration.pgcc_account_ids.mapped("dere12_cCta")
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(declaration.pgcc_account_ids)

    def test_d1106_rewrites_existing_line_and_reads_previous_opening(self):
        self.company.dere_subject_d1106 = True
        self._map_d1106_codtrib()
        self.equity_account.l10n_br_dere_reserve_invest = True
        self.env["l10n_br_dere.reserve.asset"].create(
            {
                "company_id": self.company.id,
                "id_ativo": "CDBPREV01",
                "desc_ativo": "Previous CDB",
                "account_id": self.equity_account.id,
            }
        )
        first = self._prepare_trial("2025-06")
        first.action_generate_d1106()
        first.action_generate_d1106()
        first.reserve_line_ids.write(
            {
                "dere12_vSaldoInic": 200.0,
                "dere12_vVarMensal": 10.0,
                "dere12_vPrincLiqResg": 0.0,
            }
        )
        self.assertEqual(first.reserve_line_ids.dere12_vSaldoFinal, 210.0)
        second = self._prepare_trial("2025-07")
        second.action_generate_d1106()
        self.assertEqual(second.reserve_line_ids.dere12_vSaldoInic, 210.0)

    def test_d1106_rejects_unmapped_asset_and_negative_totals(self):
        self.company.dere_subject_d1106 = True
        self._map_d1106_codtrib()
        self.env["l10n_br_dere.reserve.asset"].create(
            {
                "company_id": self.company.id,
                "id_ativo": "UNMAPPED1",
                "desc_ativo": "Unmapped",
                "account_id": self.receivable.id,
            }
        )
        declaration = self._prepare_trial("2025-08")
        with self.assertRaises(UserError):
            declaration.action_generate_d1106()
        self.env["l10n_br_dere.reserve.asset"].search(
            [("id_ativo", "=", "UNMAPPED1")]
        ).unlink()
        with self.assertRaises(ValidationError):
            self.env["l10n_br_dere.reserve.asset"].create(
                {
                    "company_id": self.company.id,
                    "id_ativo": "BAD-ID",
                    "desc_ativo": "Invalid",
                    "account_id": self.equity_account.id,
                }
            )
        self.equity_account.l10n_br_dere_reserve_invest = True
        self.env["l10n_br_dere.reserve.asset"].create(
            {
                "company_id": self.company.id,
                "id_ativo": "NEGATIVO1",
                "desc_ativo": "Negative",
                "account_id": self.equity_account.id,
            }
        )
        mapped = self._prepare_trial("2025-09")
        mapped.action_generate_d1106()
        with self.assertRaises(ValidationError):
            mapped.reserve_line_ids.write(
                {
                    "dere12_vSaldoInic": 1.0,
                    "dere12_vPrincLiqResg": 10.0,
                }
            )

    def test_d1106_skips_tiny_income_and_excludes_reserve_moves(self):
        self.company.dere_subject_d1106 = True
        self._map_d1106_codtrib()
        income = self.env["account.account"].create(
            {
                "name": "Mapped coupon",
                "code": "DERECOV",
                "account_type": "income",
                "company_ids": [Command.set(self.company.ids)],
            }
        )
        self.equity_account.l10n_br_dere_reserve_invest = True
        self.equity_account.l10n_br_dere_reserve_income_account_id = income.id
        self.env["l10n_br_dere.reserve.asset"].create(
            {
                "company_id": self.company.id,
                "id_ativo": "CDBTINY01",
                "desc_ativo": "Tiny coupon",
                "account_id": self.equity_account.id,
            }
        )
        # Income debit on the reserve move is skipped (amount <= 0.005).
        self._post_entry("2025-10-05", self.fee_account, self.equity_account, 0.01)
        self._post_entry("2025-10-08", self.equity_account, self.fee_account, 8.0)
        self._post_entry("2025-10-12", self.receivable, income, 4.0)
        declaration = self._prepare_trial("2025-10")
        declaration.action_generate_d1106()
        line = declaration.reserve_line_ids
        self.assertEqual(line.dere12_vRendPerReceb, 12.0)

    def test_deduction_validations_and_item_generation(self):
        self.company.dere_subject_d1121 = True
        declaration = self._prepare_trial("2024-11")
        with self.assertRaises(ValidationError):
            self.env["l10n_br_dere.deduction.line"].create(
                self._deduction_vals(
                    declaration,
                    dere12_vDedTotal=120.0,
                    dere12_vDed=100.0,
                )
            )
        with self.assertRaises(ValidationError):
            self.env["l10n_br_dere.deduction.line"].create(
                self._deduction_vals(
                    declaration,
                    dere12_vDedTotal=False,
                    dere12_vDed=120.0,
                )
            )
        line = self.env["l10n_br_dere.deduction.line"].create(
            self._deduction_vals(
                declaration,
                dere12_vDedTotal=40.0,
                dere12_vDed=40.0,
            )
        )
        with self.assertRaises(UserError):
            declaration._ensure_deduction_items(line)
        later = self.env["l10n_br_dere.deduction.line"].create(
            self._deduction_vals(
                declaration,
                dere12_chDFe=self._nfe_access_key(8),
                dere12_dtEmi="2024-10-15",
                dere12_vDedTotal=False,
                dere12_vDed=10.0,
            )
        )
        with self.assertRaises(UserError):
            declaration._assert_deduction_current_account(later)
        later.dere12_vDedTotal = 10.0
        with self.assertRaises(UserError):
            declaration._assert_deduction_current_account(later)

    def test_deduction_line_forbids_repeated_chdfe(self):
        self.company.dere_subject_d1121 = True
        declaration = self._prepare_trial("2024-12")
        key = self._nfe_access_key(4, "2024-12")
        self.env["l10n_br_dere.deduction.line"].create(
            self._deduction_vals(declaration, dere12_chDFe=key)
        )
        with self.assertRaises(ValidationError):
            self.env["l10n_br_dere.deduction.line"].create(
                self._deduction_vals(declaration, dere12_chDFe=key)
            )

    def test_load_deductions_clears_absence_flag_and_builds_items(self):
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
                "document_date": "2024-12-15 12:00:00",
                "document_key": self._nfe_access_key(7, period="2024-12"),
                "issuer": "partner",
                "state_edoc": "a_enviar",
            }
        )
        declaration = self._prepare_trial("2024-12")
        declaration.ind_inexist_dedu = True
        declaration.action_load_deductions()
        self.assertFalse(declaration.ind_inexist_dedu)
        line = declaration.deduction_line_ids
        line.write(
            {
                "dere12_vOper": 90.0,
                "dere12_vDedTotal": 40.0,
                "dere12_vDed": 40.0,
            }
        )
        with self.assertRaises(UserError):
            declaration._ensure_deduction_items(line)
        self.env["l10n_br_dere.deduction.item"].create(
            {
                "line_id": line.id,
                "dere12_nItem": "1",
                "dere12_vItem": 90.0,
                "dere12_vItemDedTotal": 40.0,
                "dere12_vItemDed": 40.0,
            }
        )
        declaration._ensure_deduction_items(line)
        self._accept_event(declaration, "D-1101")
        self.assertEqual(declaration.primary_action, "generate_d1121")
        declaration.action_generate_d1121()
        xml = declaration.event_ids.filtered(
            lambda ev: ev.event_type == "D-1121"
        ).xml_content
        self.assertIn("<itemDFe>", xml)
        self.assertTrue(document)

    def test_deduction_document_type_and_activity_are_required(self):
        self.company.dere_subject_d1121 = True
        declaration = self._prepare_trial("2024-01")
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_01").id,
                "partner_id": self.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                "document_date": "2024-01-15 12:00:00",
                "document_key": self._nfe_access_key(6, period="2024-01"),
                "issuer": "partner",
                "state_edoc": "a_enviar",
            }
        )
        with self.assertRaises(UserError):
            declaration._deduction_vals_from_document(document)
        self.company.dere_reg_trib_princ = "1"
        nfse = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_SE").id,
                "partner_id": self.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                "document_date": "2024-01-16 12:00:00",
                "document_key": self._nfe_access_key(5, period="2024-01"),
                "issuer": "partner",
                "state_edoc": "a_enviar",
            }
        )
        with self.assertRaises(UserError):
            declaration._deduction_vals_from_document(nfse)

    def test_closing_requires_generated_d1121_and_heals_stale_states(self):
        self.company.dere_subject_d1121 = True
        declaration = self._prepare_trial("2024-02")
        self.env["l10n_br_dere.deduction.line"].create(
            self._deduction_vals(declaration)
        )
        self.assertFalse(declaration.can_close_period)
        with self.assertRaises(UserError):
            declaration.action_generate_d1199()
        declaration.action_generate_d1121()
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1121")
        declaration.ind_inexist_dedu = True
        with self.assertRaises(UserError):
            declaration.action_generate_d1199()
        declaration.ind_inexist_dedu = False
        declaration.action_generate_d1199()
        declaration.write({"state": "closed"})
        declaration.action_generate_d1199()
        self.assertEqual(declaration.state, "trial_ok")
        self._accept_event(declaration, "D-1101")
        self._accept_event(declaration, "D-1121")
        self.assertTrue(event)
        declaration.action_discard_local_closing()
        with self.assertRaises(UserError):
            declaration.action_discard_local_closing()
        declaration.action_generate_d1199()
        self._accept_closing(declaration)
        declaration.action_mark_reopened()
        declaration.write({"state": "reopened"})
        declaration.action_mark_reopened()
        self.assertEqual(declaration.state, "closed")
        self.assertTrue(declaration._can_create_next_event("D-1198"))

    def test_cannot_regenerate_periodics_without_accepted_reopening(self):
        declaration = self._prepare_trial("2024-03")
        self._accept_event(declaration, "D-1101")
        with self.assertRaises(UserError):
            declaration._generate_d1101(tp_oper="1")
        declaration.action_replace_d1101()
        replacement = self._event(declaration, "D-1101")
        self.assertEqual(replacement.tp_oper, "2")

    def test_send_order_covers_tables_reopening_and_d1121(self):
        self.company.dere_subject_d1106 = True
        self.company.dere_subject_d1121 = True
        self._map_d1106_codtrib()
        tables = self._create_declaration("2024-04")
        tables.action_generate_tables()
        with self.assertRaises(UserError):
            tables._assert_send_order(["D-1011"])
        with self.assertRaises(UserError):
            tables._assert_send_order(["D-1198"])
        empty = self._create_declaration("2023-01")
        with self.assertRaises(UserError):
            empty._assert_d1199_send_order()
        self._accept_tables(tables)
        self._post_entry("2024-04-10", self.receivable, self.fee_account, 100.0)
        tables.action_generate_d1101()
        self.env["l10n_br_dere.deduction.line"].create(self._deduction_vals(tables))
        tables.action_generate_d1106()
        tables.action_generate_d1121()
        d1121 = tables.event_ids.filtered(lambda ev: ev.event_type == "D-1121")
        with self.assertRaises(UserError):
            tables._assert_send_order(["D-1121"])
        self._accept_event(tables, "D-1101")
        with self.assertRaises(UserError):
            tables._assert_send_order(["D-1121"])
        self._accept_event(tables, "D-1106")
        tables._assert_send_order(["D-1121"])
        tables.action_generate_d1199()
        with self.assertRaises(UserError):
            tables._assert_d1199_send_order()
        self._accept_event(tables, "D-1121")
        tables._assert_d1199_send_order()
        self.assertTrue(d1121)

    def test_send_rejects_invalid_lote_xsd(self):
        declaration = self._create_declaration("2024-05")
        declaration.action_generate_d1001()
        event = self._event(declaration, "D-1001")
        with (
            patch(
                "odoo.addons.l10n_br_dere.models.dere_table_period."
                "xsd_validator.validate_lote",
                return_value=["lote broken"],
            ),
            self.assertRaises(UserError),
        ):
            self._table_period(declaration)._send_events(event)

    def test_consult_result_and_protocol_extraction_edge_cases(self):
        declaration = self._create_declaration("2024-06")
        declaration.action_generate_d1001()
        batch = self.env["l10n_br_dere.batch"].create(
            {
                "name": "edge",
                "declaration_id": declaration.id,
                "tp_amb": "2",
                "state": "sent",
                "protocol": "PROT-EDGE",
                "event_ids": [Command.set(self._event(declaration, "D-1001").ids)],
            }
        )
        self.assertFalse(declaration._apply_consult_result(batch, ""))
        self.assertFalse(declaration._apply_consult_result(batch, "not-xml"))
        self.assertFalse(declaration._apply_consult_result(batch, "<broken"))
        self.assertFalse(declaration._apply_consult_result(batch, REJECTED_LOTE))
        self.assertEqual(batch.state, "error")
        self.assertFalse(
            declaration._apply_parsed_return(
                declaration.event_ids, {"tpEv": "D-9999", "cdRetorno": "1"}
            )
        )
        self.assertFalse(declaration._extract_protocol(False))
        self.assertFalse(declaration._extract_protocol("{bad"))
        self.assertFalse(declaration._extract_protocol("plain-text"))
        self.assertFalse(declaration._extract_protocol("<broken>"))
        self.assertEqual(
            declaration._extract_protocol(
                "<DeRE><protocoloLote>PROT-XML</protocoloLote></DeRE>"
            ),
            "PROT-XML",
        )

    @mute_logger("odoo.addons.l10n_br_dere.models.dere_batch")
    def test_batch_consult_without_protocol_and_http_errors(self):
        declaration = self._create_declaration("2024-07")
        batch = self.env["l10n_br_dere.batch"].create(
            {
                "name": "empty",
                "declaration_id": declaration.id,
                "tp_amb": "2",
            }
        )
        with self.assertRaises(UserError):
            batch.action_consult()
        self.assertFalse(batch._consult(raise_error=False))
        batch.protocol = "PROT-HTTP"
        batch.state = "sent"

        class FakeTokenError:
            status_code = 401
            text = "denied"

        class FakeHttpError:
            status_code = 503
            text = "down"

        class FakeTokenOk:
            status_code = 200
            text = ""

            def json(self):
                return {"access_token": "tok", "expires_in": 3600}

        with patch(
            "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
            return_value=FakeTokenError(),
        ):
            with self.assertRaises(UserError):
                batch._consult(raise_error=True)
            self.assertEqual(batch.state, "sent")
            self.assertFalse(batch._consult(raise_error=False))
        with (
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
                return_value=FakeTokenOk(),
            ),
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.get",
                return_value=FakeHttpError(),
            ),
        ):
            result = self.env["l10n_br_dere.receita.integra"].consult_batch(
                batch.company_id, batch.protocol
            )
            self.assertFalse(result["ok"])
            self.assertEqual(result["status_code"], 503)
            self.assertTrue(batch.company_id.dere_client_id)
            with self.assertRaises(UserError) as error:
                batch._consult(raise_error=True)
            self.assertIn("down", error.exception.args[0])
            batch.state = "sent"
            self.assertFalse(batch._consult(raise_error=False))
            self.assertEqual(batch.state, "sent")

    @mute_logger("odoo.addons.l10n_br_dere.models.dere_batch")
    def test_cron_consult_swallows_unexpected_errors(self):
        declaration = self._create_declaration("2024-08")
        batch = self.env["l10n_br_dere.batch"].create(
            {
                "name": "boom",
                "declaration_id": declaration.id,
                "tp_amb": "2",
                "state": "sent",
                "protocol": "PROT-BOOM",
            }
        )
        with patch.object(type(batch), "_consult", side_effect=RuntimeError("boom")):
            self.env["l10n_br_dere.batch"]._cron_consult_batches()

    def test_token_cache_and_cnpj_vat_fallback(self):
        client = self.env["l10n_br_dere.receita.integra"]
        frozen = fields.Datetime.now()

        class FakeTokenResp:
            status_code = 200
            text = ""

            def json(self):
                return {"access_token": "cached-token", "expires_in": 3600}

        with (
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
                return_value=FakeTokenResp(),
            ) as mocked,
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.fields.Datetime.now",
                return_value=frozen,
            ),
        ):
            first = client._get_token(self.company)
            second = self.env["l10n_br_dere.receita.integra"]._get_token(self.company)
        self.assertEqual(first, "cached-token")
        self.assertEqual(second, "cached-token")
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(
            mocked.call_args.kwargs.get("auth"), ("demo-client", "demo-secret")
        )
        stored = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(f"l10n_br_dere.token.{self.company.id}")
        )
        self.assertIn("cached-token", stored)
        self.company.partner_id.vat = False
        self.company.invalidate_recordset(["vat"])
        self.assertEqual(self.company._dere_cnpj(), "")

    def test_authorized_request_retries_once_on_401(self):
        client = self.env["l10n_br_dere.receita.integra"]
        client._clear_token(self.company)
        posts = []

        class FakeToken:
            status_code = 200
            text = ""

            def json(self):
                return {"access_token": "retry-token", "expires_in": 3600}

        class FakeApi:
            def __init__(self, status_code, text="2.000001.9"):
                self.status_code = status_code
                self.text = text

        def fake_post(url, **_kwargs):
            if "token" in url:
                return FakeToken()
            posts.append(url)
            if len(posts) == 1:
                return FakeApi(401, "expired")
            return FakeApi(200)

        with patch(
            "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
            side_effect=fake_post,
        ):
            result = client.send_batch(self.company, "<DeRE/>")
        self.assertTrue(result["ok"])
        self.assertEqual(len(posts), 2)

    def test_closed_period_locks_deduction_and_reserve_rows(self):
        self.company.dere_subject_d1106 = True
        self.company.dere_subject_d1121 = True
        self._map_d1106_codtrib()
        self.equity_account.l10n_br_dere_reserve_invest = True
        self.env["l10n_br_dere.reserve.asset"].create(
            {
                "company_id": self.company.id,
                "id_ativo": "LOCK01",
                "desc_ativo": "Locked",
                "account_id": self.equity_account.id,
            }
        )
        declaration = self._prepare_trial("2024-09")
        declaration.action_generate_d1106()
        line = self.env["l10n_br_dere.deduction.line"].create(
            self._deduction_vals(declaration)
        )
        item = self.env["l10n_br_dere.deduction.item"].create(
            {
                "line_id": line.id,
                "dere12_nItem": "1",
                "dere12_vItem": 100.0,
                "dere12_vItemDed": 100.0,
            }
        )
        declaration.action_generate_d1121()
        declaration.action_generate_d1199()
        self._accept_closing(declaration)
        with self.assertRaises(UserError):
            line.write({"dere12_vDed": 90.0})
        with self.assertRaises(UserError):
            item.write({"dere12_vItemDed": 90.0})
        with self.assertRaises(UserError):
            declaration.reserve_line_ids.write({"dere12_vVarMensal": 1.0})
        with self.assertRaises(UserError):
            line.unlink()
        with self.assertRaises(UserError):
            item.unlink()
        with self.assertRaises(UserError):
            declaration.reserve_line_ids.unlink()
        with self.assertRaises(UserError):
            declaration.trial_line_ids.unlink()
        with self.assertRaises(UserError):
            declaration.pgcc_account_ids[:1].unlink()

    def test_sent_event_rejects_non_consult_writes_and_builds_ids(self):
        declaration = self._create_declaration("2024-10")
        declaration.action_generate_d1001()
        event = self._event(declaration, "D-1001")
        event.state = "sent"
        with self.assertRaises(UserError):
            event.write({"tp_oper": "2"})
        periodic = self.env["l10n_br_dere.event"].create(
            {
                "declaration_id": declaration.id,
                "event_type": "D-1101",
                "tp_amb": "2",
                "ver_aplic": "odoo-dere-18.0",
            }
        )
        event_id = periodic._generate_event_id(
            event_type="D-1101",
            company=self.company,
            tp_amb="9",
        )
        self.assertTrue(event_id.startswith("DeRE11011"))
        self.assertTrue(xsd_validator.validate(b"<broken/>", "D-1001"))
        self.assertTrue(xsd_validator.validate_lote(b"<broken/>"))
        with self.assertRaises(ValueError):
            xsd_validator.validate("<x/>", "D-0000")
        unstructured = periodic._generate_event_id(event_type="lote")
        self.assertTrue(unstructured.startswith("A"))
        with patch.object(type(self.company), "_dere_cnpj", return_value="12"):
            with self.assertRaises(UserError):
                periodic._generate_event_id(
                    event_type="D-1101",
                    company=self.company,
                    tp_amb="2",
                )

    def test_send_and_consult_helpers_cover_empty_and_reset_paths(self):
        declaration = self._create_declaration("2023-03")
        self.assertEqual(declaration._reset_months("A"), {1})
        self.assertEqual(declaration._reset_months("S"), {1, 7})
        self.assertEqual(declaration._reset_months("Q"), {1, 5, 9})
        self.assertEqual(declaration._reset_months("T"), {1, 4, 7, 10})
        self.assertEqual(declaration._reset_months("B"), {1, 3, 5, 7, 9, 11})
        self.assertEqual(declaration._reset_months(False), set(range(1, 13)))
        self.assertEqual(declaration._reset_months("Z"), {1})
        with self.assertRaises(UserError):
            declaration._send_events(self.env["l10n_br_dere.event"])
        with self.assertRaises(UserError):
            declaration._assert_send_order(["D-1001", "D-1101"])
        with self.assertRaises(UserError):
            declaration.action_consult_results()
        trial = self._prepare_trial("2023-05")
        trial.ind_inexist_dedu = True
        with self.assertRaises(UserError):
            trial.action_generate_d1199()
        self.company.dere_client_id = False
        with self.assertRaises(UserError):
            self.env["l10n_br_dere.receita.integra"]._get_token(self.company)

    def test_consult_result_processing_and_done_states(self):
        declaration = self._create_declaration("2023-04")
        declaration.action_generate_d1001()
        batch = self.env["l10n_br_dere.batch"].create(
            {
                "name": "cd1",
                "declaration_id": declaration.id,
                "tp_amb": "2",
                "state": "sent",
                "protocol": "PROT-CD1",
                "event_ids": [Command.set(self._event(declaration, "D-1001").ids)],
            }
        )
        processing = """<?xml version="1.0" encoding="utf-8"?>
<DeRE xmlns="http://www.dere.gov.br/schemas/retornoLoteDere/v1_0_1">
  <retornoLoteEventos>
    <status>
      <cdResposta>1</cdResposta>
      <descResposta>Processing</descResposta>
    </status>
  </retornoLoteEventos>
</DeRE>
"""
        self.assertFalse(declaration._apply_consult_result(batch, processing))
        self.assertEqual(batch.state, "sent")
        done = """<?xml version="1.0" encoding="utf-8"?>
<DeRE xmlns="http://www.dere.gov.br/schemas/retornoLoteDere/v1_0_1">
  <retornoLoteEventos>
    <status>
      <cdResposta>2</cdResposta>
      <descResposta>Done</descResposta>
    </status>
  </retornoLoteEventos>
</DeRE>
"""
        self.assertTrue(declaration._apply_consult_result(batch, done))
        self.assertEqual(batch.state, "done")
        action = declaration.action_consult_results()
        self.assertEqual(action["tag"], "display_notification")
