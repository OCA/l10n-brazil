# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class StockInvoiceOnshipping(models.TransientModel):

    _inherit = 'stock.invoice.onshipping'

    @api.multi
    def _get_invoice_line_values(self, moves, invoice_values, invoice):
        move = fields.first(moves)
        values = super()._get_invoice_line_values(
            moves, invoice_values, invoice
        )
        values['sale_line_ids'] = [(6, 0, move.sale_line_id.ids)]
        return values
