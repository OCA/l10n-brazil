from odoo import models
from odoo.http import request


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_update(self, product_id, line_id=None, add_qty=0, set_qty=0, **kwargs):
        result = super()._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)

        order = request.website.sale_get_order()

        update_line_id = result.get("line_id")
        if update_line_id:
            line = order.order_line.browse(update_line_id)
            line._onchange_quantity_fiscal()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_taxes()
            line._onchange_fiscal_tax_ids()
            line._compute_product_fiscal_fields()
            line._compute_fiscal_amounts()

        return result
