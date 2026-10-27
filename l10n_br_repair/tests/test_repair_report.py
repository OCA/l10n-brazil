# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import html

from odoo import Command
from odoo.tests import TransactionCase


class TestRepairReport(TransactionCase):
    def test_report_fiscal_layout(self):
        """The printed repair order carries the fiscal data of the customer
        and the fiscal operation."""
        company = self.env.ref("base.main_company")
        company.repair_fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                "product_id": self.env.ref("product.product_product_6").id,
                "company_id": company.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": self.env.ref("product.product_product_27").id,
                            "product_uom_qty": 2.0,
                            "repair_line_type": "add",
                        }
                    )
                ],
            }
        )
        content = self.env["ir.actions.report"]._render_qweb_html(
            "repair.report_repairorder2", repair.ids
        )[0]
        page = html.fromstring(content)
        self.assertTrue(page.xpath("//div[@name='l10n_br_partner_fiscal_data']"))
        operation = page.xpath("//div[@name='informations_fiscal_operation']")
        self.assertTrue(operation)
        self.assertIn(
            repair.fiscal_operation_id.name,
            " ".join(operation[0].text_content().split()),
        )
