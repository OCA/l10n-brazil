# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import html

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

    def _render(self, report_name, records):
        content = self.env["ir.actions.report"]._render_qweb_html(
            report_name, records.ids
        )[0]
        page = html.fromstring(content)
        return page, " ".join(page.text_content().split())

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

    def test_report_fiscal_layout(self):
        """The printed order and invoice carry the fiscal data, list each
        fiscal tax once and their summary closes on the document total."""
        line = self.order.order_line.filtered("product_id.default_code")[:1]
        line.name = "Custom description"
        page, text = self._render("sale.report_saleorder", self.order)
        code = line.product_id.default_code
        self.assertIn(f"[{code}] Custom description", text)
        self.assertIn(f"CFOP {line.cfop_id.code}", text)
        self.assertTrue(page.xpath("//div[@name='l10n_br_partner_fiscal_data']"))
        self.assertIn("Document total", text)
        totals = self.order._get_report_fiscal_totals()
        self.assertAlmostEqual(totals["rows"][-1][1], self.order.amount_total)

        self.order.action_confirm()
        invoice = self.order._create_invoices()
        totals = invoice._get_report_fiscal_totals()
        self.assertAlmostEqual(totals["rows"][-1][1], invoice.amount_total)
        page, text = self._render("account.report_invoice", invoice)
        columns = [
            [" ".join(item.text_content().split()) for item in span.xpath(".//small")]
            for span in page.xpath("//span[@id='line_tax_ids']")
        ]
        self.assertTrue(columns)
        for names in columns:
            self.assertTrue(names)
            self.assertEqual(len(names), len(set(names)), names)
            self.assertFalse([n for n in names if "Dedutível" in n], names)

    def test_report_fiscal_layout_disabled(self):
        """With the options off the order keeps the summary of the core."""
        self.order.company_id.write(
            {
                "report_partner_fiscal_data": False,
                "report_line_cfop": False,
                "report_fiscal_totals": False,
            }
        )
        self.assertFalse(self.order._get_report_fiscal_totals())
        page, text = self._render("sale.report_saleorder", self.order)
        self.assertFalse(page.xpath("//div[@name='l10n_br_partner_fiscal_data']"))
        self.assertNotIn("CFOP", text)
        self.assertNotIn("Document total", text)
