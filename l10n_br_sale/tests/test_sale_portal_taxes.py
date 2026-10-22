# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import html

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestSalePortalTaxes(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.order = cls.env.ref("l10n_br_sale.lc_so_only_products")
        # Deductible taxes come in pairs that cancel each other in tax_totals
        operation = cls.order.fiscal_operation_id.with_company(cls.order.company_id)
        operation.deductible_taxes = True
        cls.order = cls.order.with_company(cls.order.company_id)
        cls.order._onchange_fiscal_operation_id()
        cls.order.order_line._compute_tax_id()
        assert cls.order.order_line.tax_id.filtered("deductible")
        cls.order.action_quotation_sent()

    def _group_amounts(self):
        groups = self.order.tax_totals["groups_by_subtotal"]
        return {
            group["tax_group_name"]: group["tax_group_amount"]
            for group_list in groups.values()
            for group in group_list
        }

    def test_tax_totals_use_fiscal_values(self):
        """The tax groups of tax_totals carry the fiscal values of the lines."""
        self.assertTrue(self.order.amount_icms_value)
        amounts = self._group_amounts()
        self.assertAlmostEqual(amounts["ICMS"], self.order.amount_icms_value)
        self.assertAlmostEqual(amounts["PIS"], self.order.amount_pis_value)
        self.assertAlmostEqual(amounts["COFINS"], self.order.amount_cofins_value)

    def test_portal_page_shows_fiscal_taxes(self):
        """The portal order page shows the fiscal values and each tax once."""
        self.order._portal_ensure_token()
        response = self.url_open(self.order.get_portal_url())
        self.assertEqual(response.status_code, 200)
        page = html.fromstring(response.content)
        totals = " ".join(page.xpath("//table[contains(@class, 'table-sm')]//text()"))
        icms = self.env["ir.qweb.field.monetary"].value_to_html(
            self.order.amount_icms_value,
            {"display_currency": self.order.currency_id},
        )
        icms_text = "".join(html.fromstring("<p>%s</p>" % icms).itertext())
        self.assertIn(" ".join(icms_text.split()), " ".join(totals.split()))
        # One entry per fiscal tax, never the deductible twin of the account tax
        self.assertNotIn("Dedutível", totals)
        for line in self.order.order_line.filtered(lambda ln: not ln.display_type):
            for tax in line.fiscal_tax_ids.filtered(
                lambda tax: tax.percent_amount or tax.value_amount
            ):
                self.assertIn(tax.name, totals)
