# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_stock_moves(self, picking):
        """Prepare the stock moves data for one order line.
        This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        values = super()._prepare_stock_moves(picking)
        for v in values:
            if self.order_id.fiscal_operation_id:
                v.update(self._prepare_br_fiscal_dict())
            if self.order_id.purchase_invoicing_policy == "stock_picking":
                v["invoice_state"] = "2binvoiced"
        return values

    @api.model
    def _prepare_purchase_order_line_from_procurement(
        self, product_id, product_qty, product_uom, company_id, values, po
    ):
        res = super()._prepare_purchase_order_line_from_procurement(
            product_id, product_qty, product_uom, company_id, values, po
        )
        if values.get("move_dest_ids"):
            for move in values.get("move_dest_ids"):
                move.fiscal_operation_id = (
                    move.fiscal_operation_id.inverse_fiscal_operation_id.id
                )

        return res
