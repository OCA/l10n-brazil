# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api, fields, _
from odoo.exceptions import Warning as UserError


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    invoice_state = fields.Selection([
        ('2binvoiced', 'To be refunded/invoiced'),
        ('none', 'No invoicing')],
        'Invoicing', required=True)

    @api.multi
    def _create_returns(self):
        """
         Creates return picking.
         @param self: The object pointer.
         @return: A dictionary which of fields with values.
        """
        picking_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']

        origin_picking = self.env['stock.picking'].browse(
            self.env.context['active_id'])
        refund_fiscal_operation = (
            origin_picking.operation_id.return_operation_id)

        if not refund_fiscal_operation:
            raise UserError(
                _('Error!'),
                _('This Fiscal Operation does not has Fiscal'
                  ' Operation for Returns!'))

        new_picking_id, pick_type_id = super(
            StockReturnPicking, self)._create_returns()

        picking = picking_obj.browse(new_picking_id)

        if self.invoice_state == '2binvoiced':

            values = {
                'operation_id': refund_fiscal_operation.id,
            }

            picking.write(values)
            for move in picking.move_lines:
                fiscal_operation = (
                    move.origin_returned_move_id.
                    operation_id.return_operation_id)
                fiscal_line_operation = (
                    move.origin_returned_move_id.
                    operation_line_id.line_refund_id)

                line_values = {
                    'invoice_state': self.invoice_state,
                    'operation_id': fiscal_operation.id,
                    'operation_line_id': fiscal_line_operation.id,
                }
                write_move = move_obj.browse(move.id)
                write_move.write(line_values)

        return new_picking_id, pick_type_id
