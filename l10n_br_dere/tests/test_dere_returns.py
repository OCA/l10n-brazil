# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, datetime

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_dere.models import xml_builder

from .common import DereCommon

SCHEMAS = "http://www.dere.gov.br/schemas"
RETURN_VERSIONS = {
    "evtRetornoTabela": "v1_0_1",
    "evtRetornoBalan": "v1_0_0",
    "evtRetornoAplicFin": "v1_0_0",
    "evtRetornoRDed": "v0_0_1",
    "evtRetornoReabert": "v0_0_1",
    "evtRetornoMensal": "v0_0_2",
}
VALID_HASH = "A" * 43 + "="


@tagged("post_install", "-at_install")
class TestDereReturns(DereCommon):
    def _event_return(self, tag, event, receipt, info_evento="", hash_value=None):
        seq = "" if tag == "evtRetornoTabela" else "<seqEvento>00</seqEvento>"
        return (
            f'<DeRE xmlns="{SCHEMAS}/{tag}/{RETURN_VERSIONS[tag]}">'
            f'<{tag} id="{event.event_id_attr}">'
            f"<ideContrib><nrInsc>{self.company._dere_cnpj_root()}</nrInsc>"
            "</ideContrib>"
            "<ideStatus><cdRetorno>1</cdRetorno>"
            "<descRetorno>Sucesso</descRetorno></ideStatus>"
            "<infoRecEv>"
            f"<nrRecibo>{receipt}</nrRecibo>{seq}"
            "<dhRecepcao>2026-12-05T12:00:00.1234567-03:00</dhRecepcao>"
            "<dhProcess>2026-12-05T12:00:01.0000000-03:00</dhProcess>"
            f"<tpEv>{event.event_type}</tpEv>"
            f"<hash>{hash_value or VALID_HASH}</hash>"
            "</infoRecEv>"
            f"{info_evento}"
            f"</{tag}>"
            "</DeRE>"
        )

    def _lot(self, *returns):
        events = "".join(
            f'<evento id="{event.event_id_attr}">{xml}</evento>'
            for event, xml in returns
        )
        return (
            f'<DeRE xmlns="{SCHEMAS}/retornoLoteDere/v1_0_1">'
            "<retornoLoteEventos>"
            "<status><cdResposta>2</cdResposta>"
            "<descResposta>Done</descResposta></status>"
            f"<retornoEventos>{events}</retornoEventos>"
            "</retornoLoteEventos>"
            "</DeRE>"
        )

    def _consult(self, parent, *returns):
        events = self.env["l10n_br_dere.event"].union(*(ev for ev, _xml in returns))
        field = (
            "table_period_id"
            if parent._name == "l10n_br_dere.table.period"
            else "declaration_id"
        )
        batch = self.env["l10n_br_dere.batch"].create(
            {
                field: parent.id,
                "tp_amb": "2",
                "state": "sent",
                "protocol": "1.000000.1",
                "event_ids": [Command.set(events.ids)],
            }
        )
        parent._apply_consult_result(batch, self._lot(*returns))
        return batch

    def _pgcc_receipt(self, declaration):
        return self._event(declaration, "D-1011").nr_recibo

    def _balan_info(self, declaration, totals="", pgcc_receipt=None):
        return (
            "<infoEvento>"
            f"<idePeriodo><perApur>{declaration.per_apur}</perApur></idePeriodo>"
            "<infoAdic><nrReciboPGCC>"
            f"{pgcc_receipt or self._pgcc_receipt(declaration)}"
            "</nrReciboPGCC></infoAdic>"
            f"{totals}"
            "</infoEvento>"
        )

    def _balan_totals(self, *groups):
        body = "".join(
            f"<gTotalCodTrib><codTrib>{code}</codTrib>"
            f"<indTribISS>{ind_trib_iss}</indTribISS>"
            f"<vApurTot>{amount:.2f}</vApurTot></gTotalCodTrib>"
            for code, ind_trib_iss, amount in groups
        )
        return f"<infoTotBalan>{body}</infoTotBalan>"

    def _fee_line(self, declaration):
        return declaration.trial_line_ids.filtered(
            lambda line: line.pgcc_account_id.account_id == self.fee_account
        )

    def _accept_d1101(self, declaration, totals="", pgcc_receipt=None):
        event = self._event(declaration, "D-1101")
        info = self._balan_info(declaration, totals, pgcc_receipt)
        receipt = self._event_receipt("D-1101", declaration.per_apur)
        self._consult(
            declaration,
            (event, self._event_return("evtRetornoBalan", event, receipt, info)),
        )
        return event

    def _mensal_info(self, declaration, balancete_receipt):
        taxes = (
            "<vIBSMun>5.00</vIBSMun><vIBSUF>5.00</vIBSUF>"
            "<vIBSTot>10.00</vIBSTot><vCBS>9.00</vCBS>"
        )
        det_bc = (
            "<detBC><codBC>2101</codBC><xDetBC>Health-plan revenue</xDetBC>"
            "<memoriaCalculo>100.00 x 10%</memoriaCalculo>"
            "<gBCIBS><vBCIBS>100.00</vBCIBS><vBCApurIBS>100.00</vBCApurIBS>"
            "<pIBSMun>5.000000</pIBSMun><vIBSMun>5.00</vIBSMun>"
            "<pIBSUF>5.000000</pIBSUF><vIBSUF>5.00</vIBSUF>"
            "<pIBS>10.000000</pIBS><vIBSTot>10.00</vIBSTot></gBCIBS>"
            "<gBCCBS><vBCCBS>100.00</vBCCBS><vBCApurCBS>100.00</vBCApurCBS>"
            "<pCBS>9.000000</pCBS><vCBS>9.00</vCBS></gBCCBS>"
            "</detBC>"
        )
        return (
            "<infoEvento>"
            f"<idePeriodo><perApur>{declaration.per_apur}</perApur></idePeriodo>"
            "<infoAdic><nrReciboBalancete>"
            f"{balancete_receipt}"
            "</nrReciboBalancete></infoAdic>"
            f"<infoTotSaude>{det_bc}<totalTributos>{taxes}</totalTributos>"
            "</infoTotSaude>"
            f"<totalTributosGeral>{taxes}</totalTributosGeral>"
            "</infoEvento>"
        )

    def _accept_d1199(self, declaration, balancete_receipt=None):
        fee = self._fee_line(declaration)
        d1101 = self._accept_d1101(
            declaration,
            self._balan_totals((self.tax_admin_fee.code, "0", fee.dere12_vApur)),
        )
        declaration.action_generate_d1199()
        event = self._event(declaration, "D-1199")
        info = self._mensal_info(declaration, balancete_receipt or d1101.nr_recibo)
        receipt = self._event_receipt("D-1199", declaration.per_apur)
        self._consult(
            declaration,
            (event, self._event_return("evtRetornoMensal", event, receipt, info)),
        )
        return event

    def _extract(self, validity=(), gaps=()):
        details = "".join(
            f"<detEvento><nrRecibo>{receipt}</nrRecibo><iniValid>{start}</iniValid>"
            + (
                f"<fimValidEfetiva>{cut}</fimValidEfetiva>"
                "<indAjusteAuto>1</indAjusteAuto>"
                if cut
                else "<indAjusteAuto>0</indAjusteAuto>"
            )
            + "</detEvento>"
            for receipt, start, cut in validity
        )
        lacunas = "".join(
            f"<detLacuna><iniLacuna>{start}</iniLacuna>"
            + (f"<fimLacuna>{end}</fimLacuna>" if end else "")
            + "</detLacuna>"
            for start, end in gaps
        )
        return f"<extratoEventos>{details}{lacunas}</extratoEventos>"

    def _table_return(self, declaration, event_type, extract):
        event = self._event(declaration, event_type)
        receipt = self._event_receipt(event_type, declaration.per_apur)
        self._consult(
            self._table_period(declaration),
            (event, self._event_return("evtRetornoTabela", event, receipt, extract)),
        )
        return event

    def _schema_messages(self, event):
        return event.message_ids.filtered(
            lambda message: "official XSD" in (message.body or "")
        )

    def test_parse_datetime_normalizes_fraction_and_offset(self):
        self.assertEqual(
            xml_builder.parse_datetime("2026-12-05T12:00:00.1234567-03:00"),
            datetime(2026, 12, 5, 15, 0, 0, 123456),
        )
        self.assertEqual(
            xml_builder.parse_datetime("2026-10-16T12:00:00Z"),
            datetime(2026, 10, 16, 12, 0, 0),
        )
        self.assertFalse(xml_builder.parse_datetime(""))
        self.assertFalse(xml_builder.parse_datetime("not a date"))

    def test_return_metadata_is_stored_per_event(self):
        declaration = self._prepare_trial()
        event = self._event(declaration, "D-1101")
        receipt = self._event_receipt("D-1101", declaration.per_apur)
        self._consult(
            declaration,
            (
                event,
                self._event_return(
                    "evtRetornoBalan", event, receipt, self._balan_info(declaration)
                ),
            ),
        )
        self.assertEqual(event.state, "accepted")
        self.assertEqual(event.nr_recibo, receipt)
        self.assertEqual(event.return_type, "D-9101")
        self.assertEqual(event.seq_evento, "00")
        self.assertEqual(event.dh_recepcao, datetime(2026, 12, 5, 15, 0, 0, 123456))
        self.assertEqual(event.dh_process, datetime(2026, 12, 5, 15, 0, 1))
        self.assertEqual(event.nr_recibo_pgcc, self._pgcc_receipt(declaration))
        self.assertIn("evtRetornoBalan", event.return_xml)
        self.assertFalse(self._schema_messages(event))

    def test_invalid_return_is_kept_and_flagged(self):
        declaration = self._prepare_trial()
        event = self._event(declaration, "D-1101")
        receipt = self._event_receipt("D-1101", declaration.per_apur)
        self._consult(
            declaration,
            (
                event,
                self._event_return(
                    "evtRetornoBalan",
                    event,
                    receipt,
                    self._balan_info(declaration),
                    hash_value="abcd",
                ),
            ),
        )
        self.assertEqual(event.state, "accepted")
        self.assertTrue(event.return_xml)
        self.assertTrue(self._schema_messages(event))

    def test_d9101_totals_match_the_trial_balance(self):
        declaration = self._prepare_trial()
        fee = self._fee_line(declaration)
        self.assertTrue(fee.dere12_vApur)
        code = self.tax_admin_fee.code
        event = self._accept_d1101(
            declaration, self._balan_totals((code, "0", fee.dere12_vApur))
        )
        self.assertEqual(len(event.total_ids), 1)
        self.assertEqual(event.total_ids.dere12_codTrib, code)
        self.assertAlmostEqual(event.total_ids.dere12_vApurTot, fee.dere12_vApur)
        self.assertAlmostEqual(event.total_ids.local_v_apur, fee.dere12_vApur)
        self.assertFalse(event.total_ids.has_difference)
        self.assertEqual(declaration.rfb_total_ids, event.total_ids)
        self.assertFalse(declaration.rfb_mismatch)

    def test_d9101_flags_differences_and_foreign_pgcc_receipt(self):
        declaration = self._prepare_trial()
        fee = self._fee_line(declaration)
        foreign = self._event_receipt("D-1011", "2026-01")
        event = self._accept_d1101(
            declaration,
            self._balan_totals(
                (self.tax_admin_fee.code, "0", fee.dere12_vApur - 10),
                ("120110007", "0", 3.0),
            ),
            pgcc_receipt=foreign,
        )
        self.assertEqual(event.state, "accepted")
        self.assertEqual(event.nr_recibo_pgcc, foreign)
        by_code = {total.dere12_codTrib: total for total in event.total_ids}
        self.assertAlmostEqual(by_code[self.tax_admin_fee.code].difference, -10.0)
        self.assertAlmostEqual(by_code["120110007"].local_v_apur, 0.0)
        self.assertTrue(declaration.rfb_mismatch)
        self.assertTrue(
            declaration.message_ids.filtered(
                lambda message: foreign in (message.body or "")
            )
        )

    def test_d9106_total_compares_reserve_lines(self):
        self.company.dere_subject_d1106 = True
        declaration = self._prepare_d1106_trial()
        declaration.action_generate_d1106()
        event = self._event(declaration, "D-1106")
        info = (
            "<infoEvento>"
            f"<idePeriodo><perApur>{declaration.per_apur}</perApur></idePeriodo>"
            f"<infoAdic><nrReciboPGCC>{self._pgcc_receipt(declaration)}"
            "</nrReciboPGCC></infoAdic>"
            "<infoTotAplicFin><vApurTot>5.00</vApurTot></infoTotAplicFin>"
            "</infoEvento>"
        )
        receipt = self._event_receipt("D-1106", declaration.per_apur)
        self._consult(
            declaration,
            (event, self._event_return("evtRetornoAplicFin", event, receipt, info)),
        )
        self.assertEqual(event.return_type, "D-9106")
        self.assertFalse(self._schema_messages(event))
        self.assertAlmostEqual(event.total_ids.dere12_vApurTot, 5.0)
        self.assertAlmostEqual(event.total_ids.local_v_apur, 0.0)
        self.assertTrue(declaration.rfb_mismatch)

    def test_d9199_records_the_ibs_cbs_assessment(self):
        declaration = self._prepare_trial()
        event = self._accept_d1199(declaration)
        self.assertEqual(event.return_type, "D-9199")
        self.assertFalse(self._schema_messages(event))
        self.assertEqual(declaration.state, "closed")
        self.assertEqual(declaration.rfb_assessment_event_id, event)
        line = declaration.tax_assessment_line_ids
        self.assertEqual(len(line), 1)
        self.assertEqual(line.regime, "2")
        self.assertEqual(line.event_id, event)
        self.assertEqual(line.dere12_codBC, "2101")
        self.assertEqual(line.dere12_memoriaCalculo, "100.00 x 10%")
        self.assertAlmostEqual(line.dere12_pIBS, 10.0)
        self.assertAlmostEqual(line.dere12_vIBSTot, 10.0)
        self.assertAlmostEqual(line.dere12_vCBS, 9.0)
        self.assertAlmostEqual(declaration.rfb_v_ibs_mun, 5.0)
        self.assertAlmostEqual(declaration.rfb_v_ibs_tot, 10.0)
        self.assertAlmostEqual(declaration.rfb_v_cbs, 9.0)
        self.assertFalse(declaration.rfb_v_is)
        self.assertEqual(
            declaration.rfb_nr_recibo_balancete,
            self._event(declaration, "D-1101").nr_recibo,
        )
        self.assertFalse(declaration.rfb_nr_recibo_aplic_fin)
        self.assertFalse(declaration.rfb_mismatch)
        html = (
            self.env["ir.actions.report"]
            ._render_qweb_html(
                "l10n_br_dere.report_dere_rfb_assessment", declaration.ids
            )[0]
            .decode()
        )
        self.assertIn(declaration.per_apur, html)
        self.assertIn("2101", html)
        self.assertIn("Trial balance receipt used", html)
        self.assertIn(declaration.rfb_nr_recibo_balancete, html)

    def test_rfb_assessment_report_requires_content(self):
        declaration = self._create_declaration()
        with self.assertRaises(UserError):
            self.env["ir.actions.report"]._render_qweb_html(
                "l10n_br_dere.report_dere_rfb_assessment", declaration.ids
            )

    def test_d9199_flags_a_foreign_trial_receipt(self):
        declaration = self._prepare_trial()
        foreign = self._event_receipt("D-1101", "2026-01")
        self._accept_d1199(declaration, balancete_receipt=foreign)
        self.assertEqual(declaration.state, "closed")
        self.assertTrue(declaration.rfb_mismatch)
        self.assertTrue(
            declaration.message_ids.filtered(
                lambda message: foreign in (message.body or "")
            )
        )
        declaration.write({"state": "reopened"})
        self.assertFalse(declaration.rfb_mismatch)
        self.assertTrue(declaration.tax_assessment_line_ids)

    def test_d9001_extract_cuts_the_period_and_reports_gaps(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        period = self._table_period(declaration)
        table = self.env["l10n_br_dere.table.period"]
        self.assertEqual(table._find_covering(self.company, date(2026, 10, 20)), period)
        receipt = self._event_receipt("D-1001", declaration.per_apur)
        foreign = self._event_receipt("D-1001", "2026-01")
        event = self._table_return(
            declaration,
            "D-1001",
            self._extract(
                validity=[
                    (receipt, "2026-10-01", "2026-10-15"),
                    (foreign, "2026-10-16", None),
                ],
                gaps=[("2026-01-01", "2026-09-30")],
            ),
        )
        self.assertEqual(event.state, "accepted")
        self.assertEqual(event.return_type, "D-9001")
        self.assertFalse(self._schema_messages(event))
        self.assertEqual(period.rfb_validity_ids.dere12_nrRecibo, receipt)
        self.assertEqual(period.fim_valid_efetiva, date(2026, 10, 15))
        self.assertEqual(len(period.rfb_extract_validity_ids), 2)
        self.assertEqual(period.rfb_gap_ids.dere12_iniLacuna, date(2026, 1, 1))
        self.assertEqual(table._find_covering(self.company, date(2026, 10, 10)), period)
        self.assertNotEqual(
            table._find_covering(self.company, date(2026, 10, 20)), period
        )
        notes = " ".join(period.message_ids.mapped("body"))
        self.assertIn(foreign, notes)
        self.assertIn("2026-01-01", notes)

    def test_d9001_extract_replaces_only_the_photo_of_its_table(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        period = self._table_period(declaration)
        d1001 = self._event_receipt("D-1001", declaration.per_apur)
        d1011 = self._event_receipt("D-1011", declaration.per_apur)
        event = self._table_return(
            declaration,
            "D-1001",
            self._extract(
                validity=[(d1001, "2026-10-01", "2026-10-15")],
                gaps=[("2026-01-01", "2026-09-30")],
            ),
        )
        self._table_return(
            declaration, "D-1011", self._extract(validity=[(d1011, "2026-10-01", None)])
        )
        self.assertEqual(period.fim_valid_efetiva, date(2026, 10, 15))
        period._apply_return_content(
            event,
            {
                "extract": {
                    "validity": [{"nrRecibo": d1001, "iniValid": "2026-10-01"}],
                    "gaps": [],
                }
            },
        )
        self.assertFalse(period.fim_valid_efetiva)
        validity = self.env["l10n_br_dere.table.validity"].search(
            [("company_id", "=", self.company.id)]
        )
        self.assertEqual(
            sorted(validity.mapped("dere12_nrRecibo")), sorted([d1001, d1011])
        )
        self.assertFalse(
            self.env["l10n_br_dere.table.gap"].search(
                [("company_id", "=", self.company.id)]
            )
        )

    def test_return_types_are_not_event_types(self):
        selection = dict(self.env["l10n_br_dere.event"]._fields["event_type"].selection)
        self.assertFalse([code for code in selection if code.startswith("D-9")])
