# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from datetime import date, datetime

from odoo.tests.common import tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon


class SpedPisCofinsEntradaMixin:
    def _declaration_july(self):
        return self._declaration("efd_pis_cofins", date(2026, 7, 1), date(2026, 7, 31))

    def _c100(self, declaration):
        """{NUM_DOC: C100} of the generated file."""
        return {rec["NUM_DOC"]: rec for rec in self._sped_records(declaration, "C100")}


@tagged("post_install", "-at_install")
class TestSpedPisCofinsEntrada(SpedPisCofinsEntradaMixin, SpedEntradaCommon):
    """How the EFD Contribuicoes books a supplier invoice (the entry)."""

    def test_c100_cod_sit_follows_the_state_of_the_document(self):
        regular, _line = self._entry_document()
        cancelled, _line = self._entry_document(state_edoc="cancelada")
        denied, _line = self._entry_document(state_edoc="denegada")
        unused, _line = self._entry_document(state_edoc="inutilizada")
        complementary, _line = self._entry_document(edoc_purpose="2")
        declaration = self._declaration_july()
        c100 = self._c100(declaration)
        self.assertEqual(
            {
                doc.document_number: c100[doc.document_number]["COD_SIT"]
                for doc in (regular, cancelled, complementary)
            },
            {
                regular.document_number: "00",
                cancelled.document_number: "02",
                complementary.document_number: "06",
            },
        )
        # the codes 04 and 05 were discontinued in the Guia Pratico from
        # 01/2023: a denied note and an unused number have no C100
        self.assertNotIn(denied.document_number, c100)
        self.assertNotIn(unused.document_number, c100)
        text = declaration._generate_sped_text()
        self.assertNotIn(denied.document_key, text)
        self.assertNotIn(unused.document_key, text)

    def test_c100_of_a_cancelled_document_only_has_what_the_guide_allows(self):
        cancelled, _line = self._entry_document(state_edoc="cancelada")
        declaration = self._declaration_july()
        rec = self._c100(declaration)[cancelled.document_number]
        self.assertEqual(rec["COD_SIT"], "02")
        self.assertEqual(rec["CHV_NFE"], cancelled.document_key)
        for name in ("COD_PART", "DT_DOC", "DT_E_S", "VL_DOC", "VL_PIS", "VL_COFINS"):
            self.assertEqual(rec[name], "", f"{name} must be blank")
        self.assertNotIn("|C170|", declaration._generate_sped_text())

    def test_the_entry_received_after_its_emission_is_regular(self):
        late, _line = self._entry_document(
            document_date=datetime(2026, 6, 20, 12, 0),
            date_in_out=datetime(2026, 7, 5, 12, 0),
        )
        late_complementary, _line = self._entry_document(
            document_date=datetime(2026, 6, 21, 12, 0),
            date_in_out=datetime(2026, 7, 6, 12, 0),
            edoc_purpose="2",
        )
        c100 = self._c100(self._declaration_july())
        self.assertEqual(c100[late.document_number]["COD_SIT"], "00")
        self.assertEqual(c100[late_complementary.document_number]["COD_SIT"], "06")

    def test_the_period_and_the_entry_date_of_an_entry(self):
        """The entry is booked in the month it came in, with DT_DOC the emission
        and DT_E_S the entry date (it used to repeat the emission). An outgoing
        document keeps the emission date for both."""
        entry, _line = self._entry_document(
            document_date=datetime(2026, 6, 28, 12, 0),
            date_in_out=datetime(2026, 7, 3, 12, 0),
        )
        out, _line = self._entry_document(
            document_date=datetime(2026, 6, 28, 12, 0),
            date_in_out=datetime(2026, 7, 3, 12, 0),
            operation="fo_venda",
            operation_line="fo_venda_venda",
            imported=False,
        )
        july = self._c100(self._declaration_july())
        self.assertIn(entry.document_number, july)
        self.assertNotIn(out.document_number, july)
        self.assertEqual(july[entry.document_number]["DT_DOC"], "28062026")
        self.assertEqual(july[entry.document_number]["DT_E_S"], "03072026")
        june = self._c100(
            self._declaration("efd_pis_cofins", date(2026, 6, 1), date(2026, 6, 30))
        )
        self.assertNotIn(entry.document_number, june)
        self.assertEqual(june[out.document_number]["DT_DOC"], "28062026")
        self.assertEqual(june[out.document_number]["DT_E_S"], "28062026")

    def _c170(self, declaration):
        records = self._sped_records(declaration, "C170")
        self.assertEqual(len(records), 1)
        return records[0]

    @staticmethod
    def _number(text):
        return float(text.replace(",", ".") or 0)

    def test_c170_has_the_37_fields_of_the_pva_layout(self):
        """The PVA 6.2.0 C170 of the EFD Contribuicoes has 37 fields (REG, the
        ICMS and IPI block, PIS, COFINS and COD_CTA), with CST_PIS in the 25th."""
        self._entry_document()
        text = self._declaration_july()._generate_sped_text()
        line = next(ln for ln in text.splitlines() if ln.startswith("|C170|"))
        fields = line.split("|")[1:-1]
        self.assertEqual(len(fields), 37)
        self.assertEqual(fields[24], "70")  # CST_PIS of the cumulative entry
        self.assertEqual(fields[30], "70")  # CST_COFINS

    def test_the_cumulative_entry_cst_reaches_the_c170(self):
        """Lucro presumido: the C170 carries CST 70, not the CST of the supplier."""
        self._entry_document()
        c170 = self._c170(self._declaration_july())
        self.assertEqual(c170["CST_PIS"], "70")
        self.assertEqual(c170["CST_COFINS"], "70")

    def test_the_cumulative_company_books_the_entry_without_credit(self):
        """Lucro presumido: CST 70, no base, rate or value, no credit nature."""
        _doc, line = self._entry_document()
        c170 = self._c170(self._declaration_july())
        self.assertEqual(c170["CST_PIS"], "70")
        self.assertEqual(c170["CST_COFINS"], "70")
        for name in ("VL_BC_PIS", "ALIQ_PIS", "VL_PIS", "VL_BC_COFINS", "VL_COFINS"):
            self.assertEqual(self._number(c170[name]), 0.0, name)
        self.assertEqual(line.pis_cst_id.code, "01", "the file's CST is not touched")

    def test_the_c100_carries_the_pis_and_cofins_of_its_c170(self):
        """Lucro presumido: the header is what the items carry (no PIS or COFINS
        without credit right), not the PIS and COFINS of the supplier's note."""
        document, _line = self._entry_document()
        self.assertEqual(document.amount_pis_value, 16.5)
        declaration = self._declaration_july()
        c100 = self._c100(declaration)[document.document_number]
        c170 = self._c170(declaration)
        for name in ("VL_PIS", "VL_COFINS"):
            self.assertEqual(self._number(c100[name]), self._number(c170[name]), name)
            self.assertEqual(self._number(c100[name]), 0.0, name)


@tagged("post_install", "-at_install")
class TestSpedPisCofinsEntradaNonCumulative(
    SpedPisCofinsEntradaMixin, SpedEntradaCommon
):
    """The entry in a company of the non-cumulative regime."""

    profit_calculation = "real"

    def _c170(self, declaration):
        records = self._sped_records(declaration, "C170")
        self.assertEqual(len(records), 1)
        return records[0]

    def test_the_credit_entry_cst_reaches_the_c170(self):
        self._entry_document()
        c170 = self._c170(self._declaration_july())
        self.assertEqual(c170["CST_PIS"], "50")
        self.assertEqual(c170["CST_COFINS"], "50")

    def test_the_credit_cst_and_values_are_booked(self):
        self._entry_document()
        c170 = self._c170(self._declaration_july())
        self.assertEqual(c170["CST_PIS"], "50")
        self.assertEqual(c170["CST_COFINS"], "50")
        self.assertEqual(c170["VL_BC_PIS"], "1000,00")
        self.assertEqual(c170["VL_PIS"], "16,50")
        self.assertEqual(c170["VL_COFINS"], "76,00")
