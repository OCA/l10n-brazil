# Copyright (C) 2020  Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        values = super()._get_new_picking_values()
        values.update(self.sale_line_id.order_id._prepare_br_fiscal_dict())
        return values
