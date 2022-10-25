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
                for line in purchase.order_line:
                    price_unit = line.price_unit
                    line._onchange_product_id_fiscal()
                    line.price_unit = price_unit
                    line._onchange_fiscal_operation_id()
                    line._onchange_fiscal_operation_line_id()
        return result

    def _prepare_purchase_order_line(
        self, product_id, product_qty, product_uom, values, po, partner
    ):
        values = super()._prepare_purchase_order_line(
            product_id, product_qty, product_uom, values, po, partner
        )
        if values.get("move_dest_ids"):
            move_ids = [mv[1] for mv in values.get("move_dest_ids")]
            moves = self.env["stock.move"].browse(move_ids)
            for m in moves:
                values[
                    "fiscal_operation_id"
                ] = m.fiscal_operation_id.inverse_fiscal_operation_id.id
        return values
