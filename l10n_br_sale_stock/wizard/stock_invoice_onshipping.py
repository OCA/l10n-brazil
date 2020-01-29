# -*- coding: utf-8 -*-
# @ 2019 Akretion - www.akretion.com.br -
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    @api.multi
    def _build_invoice_values_from_pickings(self, pickings):
        result = {}
        picking = fields.first(pickings)
        comment = ''

        if picking.fiscal_position_id.inv_copy_note:
            comment += picking.fiscal_position_id.note or ''
        if picking.sale_id and picking.sale_id.copy_note:
            comment += picking.sale_id.note or ''
        if picking.note:
            comment += ' - ' + picking.note

        result['comment'] = comment

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
        result = {}
        values = super(StockInvoiceOnshipping, self
                       )._get_invoice_line_values(moves, invoice)
        move = fields.first(moves)
        if move.procurement_id and move.procurement_id.sale_line_id:
            result['partner_order'] = \
                move.procurement_id.sale_line_id.customer_order
            result['partner_order_line'] = \
                move.procurement_id.sale_line_id.customer_order_line
        values.update(result)
        values = self._simulate_invoice_line_onchange(values)
        return values
