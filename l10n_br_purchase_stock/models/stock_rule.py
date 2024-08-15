# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _run_buy(self, procurements):
        result = super()._run_buy(procurements)

        for procurement, _rule in procurements:
            purchases = self.env["purchase.order"].search(
                [("origin", "=", procurement.origin), ("state", "=", "draft")]
            )
            for purchase in purchases:
                if purchase.fiscal_operation_id:
                    for line in purchase.order_line:
                        price_unit = line.price_unit
                        line._onchange_product_id_fiscal()
                        line.price_unit = price_unit

        return result
