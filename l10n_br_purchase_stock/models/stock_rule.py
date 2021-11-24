# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _run_buy(
        self, product_id, product_qty, product_uom, location_id, name, origin, values
    ):
        super()._run_buy(
            product_id, product_qty, product_uom, location_id, name, origin, values
        )
        purchases = self.env["purchase.order"].search([("origin", "=", origin)])
        for purchase in purchases:
            for line in purchase.order_line:
                line._onchange_product_id_fiscal()
                line._onchange_fiscal_operation_id()
                line._onchange_fiscal_operation_line_id()

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
