# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestImportedTaxOverride(AccountMoveBRCommon):
    chart_template = "generic_coa"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["account.chart.template"].load_fiscal_taxes(
            companies=[cls.company_data["company"]]
        )
        cls.configure_normal_company_taxes()

        cls.move = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
        )
        cls.line = cls.move.invoice_line_ids[0]
        cls.fiscal_line = cls.line.fiscal_document_line_id

    def test_imported_tax_is_split_between_repartition_lines(self):
        """The imported value is shared by factor, not repeated per entry."""
        self.fiscal_line.write({"icms_value": 100.0, "icms_base": 1000.0})
        tax = self._icms_account_tax()
        first, second = self._split_tax_repartition(tax, 60, 40)

        taxes = [
            {
                "id": tax.id,
                "name": tax.name,
                "amount": 0.0,
                "base": 0.0,
                "tax_repartition_line_id": first.id,
            },
            {
                "id": tax.id,
                "name": tax.name,
                "amount": 0.0,
                "base": 0.0,
                "tax_repartition_line_id": second.id,
            },
        ]
        self.line._override_taxes_from_import(taxes, self.fiscal_line, 1)

        self.assertAlmostEqual(taxes[0]["amount"], 60.0, places=2)
        self.assertAlmostEqual(taxes[1]["amount"], 40.0, places=2)
        self.assertAlmostEqual(
            sum(t["amount"] for t in taxes),
            100.0,
            places=2,
            msg="the imported ICMS must be counted once across repartition lines",
        )

    def test_imported_tax_uses_the_fiscal_tax_group_mapping(self):
        """The account.tax to Brazilian tax link is the fiscal tax group."""
        self.fiscal_line.write({"ipi_value": 42.0, "ipi_base": 420.0})
        tax = self._account_tax_by_domain("ipi")
        taxes = [
            {"id": tax.id, "name": "whatever the name is", "amount": 0.0, "base": 0.0}
        ]

        self.line._override_taxes_from_import(taxes, self.fiscal_line, 1)

        self.assertAlmostEqual(taxes[0]["amount"], 42.0, places=2)
        self.assertAlmostEqual(taxes[0]["base"], 420.0, places=2)

    def test_withholding_tax_is_cleared_on_import(self):
        """The XML does not carry withholding per item, so it must be zeroed."""
        taxes = [{"name": "COFINS WH", "amount": 7.0, "base": 70.0}]

        self.line._override_taxes_from_import(taxes, self.fiscal_line, 1)

        self.assertEqual(taxes[0]["amount"], 0.0)
        self.assertEqual(taxes[0]["base"], 0.0)

    def _account_tax_by_domain(self, tax_domain):
        tax = self.env["account.tax"].search(
            [
                ("company_id", "=", self.env.company.id),
                ("tax_group_id.fiscal_tax_group_id.tax_domain", "=", tax_domain),
            ],
            limit=1,
        )
        self.assertTrue(tax, f"no account.tax found for the {tax_domain} fiscal group")
        return tax

    def _icms_account_tax(self):
        return self._account_tax_by_domain("icms")

    def _split_tax_repartition(self, tax, first_percent, second_percent):
        """Turn a single tax repartition line into two, sharing the same tax."""
        first = tax.repartition_line_ids.filtered(
            lambda rep: rep.repartition_type == "tax" and rep.document_type == "invoice"
        )[:1]
        self.assertTrue(first, "the tax is expected to have a tax repartition line")
        second = first.copy({"factor_percent": second_percent})
        first.factor_percent = first_percent
        tax.invalidate_recordset()
        return first, second
