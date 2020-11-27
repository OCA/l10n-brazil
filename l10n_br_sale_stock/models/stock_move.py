# Copyright (C) 2020  Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _get_price_unit_invoice(self, inv_type, partner, qty=1):
        result = super()._get_price_unit_invoice(inv_type, partner, qty)
        if self.sale_line_id.price_unit != result:
            return self.sale_line_id.price_unit
        return result

    def _get_new_picking_values(self):
        values = super()._get_new_picking_values()
        values.update(self.sale_line_id.order_id._prepare_br_fiscal_dict())
        return values

    def _split(self, qty, restrict_partner_id=False):
        new_move_id = super()._split(qty, restrict_partner_id)
        self._onchange_commercial_quantity()
        self._onchange_fiscal_taxes()
        return new_move_id
