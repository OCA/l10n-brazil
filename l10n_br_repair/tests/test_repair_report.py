# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import html

from odoo.tests import TransactionCase


class TestRepairReport(TransactionCase):
    def test_report_fiscal_layout(self):
        """The printed repair order carries the fiscal data and its summary
        closes on the total of the order."""
        repair = self.env.ref("l10n_br_repair.main_so_product_service")
        totals = repair._get_report_fiscal_totals()
        self.assertAlmostEqual(totals["rows"][-1][1], repair.amount_total)
        content = self.env["ir.actions.report"]._render_qweb_html(
            "repair.report_repairorder2", repair.ids
        )[0]
        page = html.fromstring(content)
        text = " ".join(page.text_content().split())
        self.assertTrue(page.xpath("//div[@name='l10n_br_partner_fiscal_data']"))
        self.assertTrue(page.xpath("//div[@name='informations_fiscal_operation']"))
        self.assertIn("Document total", text)
        self.assertIn(f"CFOP {repair.operations[:1].cfop_id.code}", text)
