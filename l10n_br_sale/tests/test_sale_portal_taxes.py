# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import html

from odoo.tests import HttpCase, tagged

from .tools import load_sale_fixture_files


@tagged("post_install", "-at_install")
class TestSalePortalTaxes(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_sale_fixture_files(cls.env)
        cls.order = cls.env.ref("l10n_br_sale.lc_so_only_products")
        # Deductible taxes come in pairs that cancel each other in tax_totals
        operation = cls.order.fiscal_operation_id.with_company(cls.order.company_id)
        operation.deductible_taxes = True
        cls.order = cls.order.with_company(cls.order.company_id)
        cls.order._onchange_fiscal_operation_id()
        cls.order.order_line._compute_tax_ids()
        assert cls.order.order_line.tax_ids.filtered("deductible")
        cls.order.action_quotation_sent()

    def _group_amounts(self):
        # Odoo 18 restructured tax_totals: subtotals[] -> tax_groups[], keyed
        # by group_name, the amount being tax_amount_currency (the 16.0
        # groups_by_subtotal/tax_group_amount mapping no longer exists).
        return {
            group["group_name"]: group["tax_amount_currency"]
            for subtotal in self.order.tax_totals["subtotals"]
            for group in subtotal["tax_groups"]
        }

    def test_tax_totals_use_fiscal_values(self):
        """The tax groups of tax_totals carry the fiscal values of the lines."""
        self.assertTrue(self.order.amount_icms_value)
        amounts = self._group_amounts()
        self.assertAlmostEqual(amounts["ICMS"], self.order.amount_icms_value)
        self.assertAlmostEqual(amounts["PIS"], self.order.amount_pis_value)
        self.assertAlmostEqual(amounts["COFINS"], self.order.amount_cofins_value)

    def test_portal_page_shows_fiscal_taxes(self):
        """The portal lists the fiscal taxes of the line, never the deductible twin.

        The per-line tax cell is core markup and Odoo decides on its own whether
        to render it for a given visitor, so what is asserted on the rendered page
        is the invariant this module owns (the deductible twin never shows up),
        and the replacement itself is asserted on the inherited arch.
        """
        view = self.env.ref("l10n_br_sale.sale_order_portal_content_l10n_br_sale")
        arch = view.arch
        self.assertIn("fiscal_tax_ids", arch)
        # the account taxes only survive as the non-BR fallback branch
        self.assertIn("x.description or x.name", arch)

        self.order._portal_ensure_token()
        response = self.url_open(self.order.get_portal_url())
        self.assertEqual(response.status_code, 200)
        page_text = " ".join(html.fromstring(response.content).itertext())
        self.assertNotIn("Dedutível", page_text)
