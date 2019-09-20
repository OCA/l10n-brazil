# -*- coding: utf-8 -*-
# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    @api.multi
    def _build_invoice_values_from_pickings(self, pickings):
        result = {}
        picking = fields.first(pickings)
        result['purchase_id'] = picking.purchase_id.id
        values = super(StockInvoiceOnshipping, self
                       )._build_invoice_values_from_pickings(pickings)
        values.update(result)

        return values

    @api.multi
    def _get_invoice_line_values(self, moves, invoice):
        """
        Create invoice line values from given moves
        :param moves: stock.move
        :param invoice: account.invoice
        :return: dict
        """
        values = super(StockInvoiceOnshipping, self
                       )._get_invoice_line_values(
            moves, invoice)
        move = fields.first(moves)
        values['purchase_line_id'] = move.purchase_line_id.id

        return values
