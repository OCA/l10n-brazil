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

    def test_tax_kind_from_the_name(self):
        """Without an account.tax, the kind comes from the name of the entry."""
        cases = {
            "ICMS ST": "icmsst",
            "ICMS": "icms",
            "IPI": "ipi",
            "PIS": "pis",
            "COFINS": "cofins",
            "ISSQN": "issqn",
            "IBS": "ibs",
            "CBS": "cbs",
            "ISS Retido": "",
            "Outra taxa": "",
        }
        for name, kind in cases.items():
            with self.subTest(name=name):
                self.assertEqual(self.line._resolve_tax_kind({"name": name}), kind)

    def test_tax_kind_from_the_fiscal_tax(self):
        """An account.tax linked to fiscal taxes takes their domain, whatever
        the name of the entry, also when only the repartition line is known."""
        tax = self._account_tax_by_domain("ipi")
        self.assertTrue(tax.fiscal_tax_ids)
        kind = tax.fiscal_tax_ids[0].tax_domain
        self.assertEqual(self.line._resolve_tax_kind({"id": tax.id, "name": "x"}), kind)
        repartition = tax.repartition_line_ids[:1]
        self.assertEqual(
            self.line._resolve_tax_kind(
                {"name": "x", "tax_repartition_line_id": repartition.id}
            ),
            kind,
        )

    def test_tax_without_fiscal_group_falls_back_to_the_name(self):
        """An account.tax with no fiscal tax group is matched by its name."""
        self.fiscal_line.write({"icms_value": 18.0, "icms_base": 100.0})
        tax = self.env["account.tax"].create(
            {
                "name": "ICMS sem grupo fiscal",
                "amount": 18.0,
                "company_id": self.env.company.id,
            }
        )
        self.assertFalse(tax.tax_group_id.fiscal_tax_group_id)
        taxes = [{"id": tax.id, "name": tax.name, "amount": 0.0, "base": 0.0}]

        self.line._override_taxes_from_import(taxes, self.fiscal_line, 1)

        self.assertAlmostEqual(taxes[0]["amount"], 18.0, places=2)
        self.assertAlmostEqual(taxes[0]["base"], 100.0, places=2)

    def test_brazilian_engine_needs_a_saved_line(self):
        """A line not saved yet has no fiscal taxes: the native computation
        fills the tax details."""
        base_line = self.move._prepare_product_base_line_for_taxes_computation(
            self.line
        )
        base_line["record"] = self.env["account.move.line"].new(
            {"move_id": self.move.id}
        )
        self.env["account.tax"]._add_br_tax_details_in_base_line(
            base_line, self.env.company
        )
        self.assertIn("tax_details", base_line)

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
