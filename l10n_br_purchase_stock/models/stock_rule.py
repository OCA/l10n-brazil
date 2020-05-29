# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _prepare_purchase_order(self, product_id, product_qty, product_uom,
                                origin, values, partner):
        values = super()._prepare_purchase_order(
            product_id, product_qty, product_uom, origin, values, partner)
        import pudb; pudb.set_trace()
        return values

    @api.multi
    def _prepare_purchase_order_line(self, product_id, product_qty,
                                     product_uom, values, po, partner):
        values = super()._prepare_purchase_order_line(
            product_id, product_qty, product_uom, company_id, values,
            po, partner)
        import pudb; pudb.set_trace()
        return values
