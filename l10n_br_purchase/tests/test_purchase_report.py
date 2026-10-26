# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import html

from odoo.tests import TransactionCase


class TestPurchaseReport(TransactionCase):
    def test_report_fiscal_layout(self):
        """The printed order lists the fiscal taxes and its summary closes on
        the document total."""
        order = self.env.ref("l10n_br_purchase.lp_po_only_products")
        totals = order._get_report_fiscal_totals()
        self.assertAlmostEqual(totals["rows"][-1][1], order.amount_total)
        content = self.env["ir.actions.report"]._render_qweb_html(
            "purchase.report_purchaseorder", order.ids
        )[0]
        page = html.fromstring(content)
        names = [
            " ".join(item.text_content().split())
            for item in page.xpath("//td[@name='td_taxes']//small")
        ]
        fiscal_names = order.order_line.fiscal_tax_ids.filtered(
            lambda tax: tax.percent_amount or tax.value_amount
        ).mapped("name")
        self.assertTrue(names)
        self.assertFalse(set(names) - set(fiscal_names), names)
