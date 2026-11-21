# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

import calendar
from datetime import date, datetime

from odoo.tests.common import tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon


class EntradaHelpers:
    def _declaration_july(self):
        return self._declaration("efd_icms_ipi", date(2026, 7, 1), date(2026, 7, 31))

    def _c100(self, declaration):
        """{NUM_DOC: C100} of the generated file."""
        return {rec["NUM_DOC"]: rec for rec in self._sped_records(declaration, "C100")}

    def _c170(self, declaration):
        records = self._sped_records(declaration, "C170")
        self.assertEqual(len(records), 1)
        return records[0]

    def _opt_in(self, value=True):
        """The company books its entries by the creditability map."""
        if "stock_valuation_via_stock_price" not in self.company._fields:
            self.skipTest("l10n_br_stock_account is not installed")
        self.company.stock_valuation_via_stock_price = value

    def _assess_icms_of_july(self, month=7, post=True):
        """The assessment of the month by the normal path: compute from the ledger,
        post."""
        group = self.env["account.tax.group"].search(
            [
                (
                    "fiscal_tax_group_id",
                    "=",
                    self.env.ref("l10n_br_fiscal.tax_group_icms").id,
                )
            ],
            limit=1,
        )
        if not group.with_company(self.company).property_tax_payable_account_id:
            payable = self.env["account.account"].create(
                {
                    "name": "ICMS a recolher",
                    "code": "ICMSPAY",
                    "account_type": "liability_current",
                    "company_id": self.company.id,
                }
            )
            receivable = self.env["account.account"].create(
                {
                    "name": "ICMS a recuperar",
                    "code": "ICMSREC",
                    "account_type": "asset_current",
                    "company_id": self.company.id,
                }
            )
            group.with_company(self.company).write(
                {
                    "property_tax_payable_account_id": payable.id,
                    "property_tax_receivable_account_id": receivable.id,
                }
            )
        assessment = self.env["l10n_br_tax.assessment"].create(
            {
                "company_id": self.company.id,
                "tax_group_id": group.id,
                "date_from": date(2026, month, 1),
                "date_to": date(2026, month, calendar.monthrange(2026, month)[1]),
            }
        )
        assessment.action_compute()
        if post:
            assessment.action_post()
        return assessment

    @staticmethod
    def _number(text):
        return float(text.replace(",", ".") or 0)


@tagged("post_install", "-at_install")
class TestSpedEfdIcmsIpiEntrada(EntradaHelpers, SpedEntradaCommon):
    """How the EFD ICMS/IPI books a supplier invoice (the entry)."""

    # A. COD_SIT

    def test_c100_cod_sit_follows_the_state_of_the_document(self):
        """state_fiscal is only written on cancellation: the situation comes
        from the state of the document and from its purpose."""
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
        cancelled.manual_fiscal_additional_data = "Observacao do documento cancelado"
        declaration = self._declaration_july()
        rec = self._c100(declaration)[cancelled.document_number]
        self.assertEqual(rec["COD_SIT"], "02")
        self.assertEqual(rec["COD_MOD"], "55")
        self.assertEqual(rec["SER"], "1")
        self.assertEqual(rec["CHV_NFE"], cancelled.document_key)
        for name in ("COD_PART", "DT_DOC", "DT_E_S", "VL_DOC", "VL_ICMS", "VL_IPI"):
            self.assertEqual(rec[name], "", f"{name} must be blank")
        # and no item nor analytic register under it
        text = declaration._generate_sped_text()
        self.assertNotIn("|C170|", text)
        self.assertNotIn("|C190|", text)
        self.assertNotIn("|C195|", text)

    def test_the_entry_received_after_its_emission_is_regular(self):
        """Emitted in June and received in July is a regular entry of July (00,
        06 if complementary): 01 and 07 are for a document booked outside the
        period of its entry date, and the PVA refuses 01 with DT_E_S in the period."""
        late, _line = self._entry_document(
            document_date=datetime(2026, 6, 20, 12, 0),
            date_in_out=datetime(2026, 7, 5, 12, 0),
        )
        late_complementary, _line = self._entry_document(
            document_date=datetime(2026, 6, 21, 12, 0),
            date_in_out=datetime(2026, 7, 6, 12, 0),
            edoc_purpose="2",
        )
        on_time, _line = self._entry_document(
            document_date=datetime(2026, 7, 2, 12, 0),
            date_in_out=datetime(2026, 7, 5, 12, 0),
        )
        c100 = self._c100(self._declaration_july())
        self.assertEqual(c100[late.document_number]["COD_SIT"], "00")
        self.assertEqual(c100[late_complementary.document_number]["COD_SIT"], "06")
        self.assertEqual(c100[on_time.document_number]["COD_SIT"], "00")

    # B. date and period of the entry

    def test_the_period_of_an_entry_is_the_one_of_the_entry_date(self):
        """Emitted in June, entered in July: it is in the July book only; DT_DOC
        stays the emission and DT_E_S is the entry date. Outgoing documents keep
        the emission date for the period."""
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
            self._declaration("efd_icms_ipi", date(2026, 6, 1), date(2026, 6, 30))
        )
        self.assertNotIn(entry.document_number, june)
        self.assertIn(out.document_number, june)

    # C. D. E. items of the entry

    def test_c170_item_and_unit_are_the_ones_of_the_company(self):
        """COD_ITEM and UNID are the code of the 0200 and the unit of the 0190,
        not the ones the supplier wrote."""
        _doc, line = self._entry_document()
        declaration = self._declaration_july()
        c170 = self._c170(declaration)
        self.assertEqual(c170["COD_ITEM"], "prod_a")
        self.assertEqual(c170["UNID"], line.uom_id.code)
        self.assertEqual(
            [rec["COD_ITEM"] for rec in self._sped_records(declaration, "0200")],
            ["prod_a"],
        )
        self.assertIn(
            line.uom_id.code,
            [rec["UNID"] for rec in self._sped_records(declaration, "0190")],
        )

    def test_c170_quantity_is_the_commercial_one_of_the_unit(self):
        """QTD is in the UNID of the line (the 0190): 10 boxes, not the 120
        units of the tax unit the supplier declared next to them."""
        dozen = self.env.ref("uom.product_uom_dozen")
        dozen.code = "DZ"
        self._entry_document(
            line_vals={
                "quantity": 10,
                "uom_id": dozen.id,
                "uot_id": self.env.ref("uom.product_uom_unit").id,
                "fiscal_quantity": 120.0,
            }
        )
        declaration = self._declaration_july()
        c170 = self._c170(declaration)
        self.assertEqual(self._number(c170["QTD"]), 10.0)
        self.assertEqual(c170["UNID"], "DZ")
        self.assertIn(
            "DZ", [rec["UNID"] for rec in self._sped_records(declaration, "0190")]
        )

    def test_c170_and_c190_carry_the_entry_cfop(self):
        """The supplier wrote 6102; the books carry the entry CFOP."""
        self._entry_document(partner_cfop="6102")
        declaration = self._declaration_july()
        self.assertEqual(self._c170(declaration)["CFOP"], "2102")
        self.assertEqual(
            [rec["CFOP"] for rec in self._sped_records(declaration, "C190")], ["2102"]
        )

    def test_the_cumulative_company_books_the_entry_without_pis_cofins(self):
        """Lucro presumido: CST 70 (acquisition without credit right) and no
        base, rate or value; the CST of the supplier stays on the line."""
        _doc, line = self._entry_document()
        c170 = self._c170(self._declaration_july())
        self.assertEqual(c170["CST_PIS"], "70")
        self.assertEqual(c170["CST_COFINS"], "70")
        for name in ("VL_BC_PIS", "ALIQ_PIS", "VL_PIS", "VL_BC_COFINS", "VL_COFINS"):
            self.assertEqual(self._number(c170[name]), 0.0, name)
        self.assertEqual(line.entry_pis_cst_id.code, "70")
        self.assertEqual(line.pis_cst_id.code, "01", "the file's CST is not touched")


@tagged("post_install", "-at_install")
class TestSpedEfdIcmsIpiEntradaNonCumulative(EntradaHelpers, SpedEntradaCommon):
    """The same entry in a company of the non-cumulative regime."""

    profit_calculation = "real"

    def test_the_non_cumulative_company_books_the_credit_cst(self):
        _doc, line = self._entry_document()
        c170 = self._c170(self._declaration_july())
        self.assertEqual(c170["CST_PIS"], "50")
        self.assertEqual(c170["CST_COFINS"], "50")
        self.assertEqual(self._number(c170["VL_PIS"]), 16.5)
        self.assertEqual(self._number(c170["VL_COFINS"]), 76.0)
        self.assertEqual(line.pis_cst_id.code, "01", "the file's CST is not touched")
