# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# Copyright 2023 KMEE (Renan Hiroki Bastos <renan.hiroki@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    partner_uom_factor = fields.Float(string="Partner UOM Factor")

    def _prepare_stock_move_vals(
        self, picking, price_unit, product_uom_qty, product_uom
    ):
        res = super()._prepare_stock_move_vals(
            picking, price_unit, product_uom_qty, product_uom
        )

        if self.partner_uom_factor:
            res["product_uom_qty"] = product_uom_qty * self.partner_uom_factor

        return res
