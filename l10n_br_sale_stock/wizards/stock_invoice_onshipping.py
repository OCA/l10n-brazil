# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class StockInvoiceOnshipping(models.TransientModel):

    _inherit = 'stock.invoice.onshipping'

    @api.multi
    def _simulate_invoice_line_onchange(self, values):
        """
        Simulate onchange for invoice line
        :param values: dict
        :return: dict
        """
        price_unit = values.pop('price_unit')
        new_values = super()._simulate_invoice_line_onchange(values.copy())
        line = self.env['account.invoice.line'].new(new_values.copy())
        line.price_unit = price_unit
        line._compute_price()
        new_values.update(line._convert_to_write(line._cache))
        values.update(new_values)
        return values

    @api.multi
    def _get_invoice_line_values(self, moves, invoice_values, invoice):
        move = fields.first(moves)
        values = super()._get_invoice_line_values(
            moves, invoice_values, invoice
        )
        values['sale_line_ids'] = [(6, 0, move.sale_line_id.ids)]
        return values
