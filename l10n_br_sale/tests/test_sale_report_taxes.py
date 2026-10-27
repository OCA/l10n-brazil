# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleReportTaxes(TransactionCase):
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
        tax_totals = self.order.tax_totals
        self.assertAlmostEqual(
            tax_totals["base_amount_currency"] + sum(amounts.values()),
            tax_totals["total_amount_currency"],
        )
