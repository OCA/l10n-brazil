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
    def _fiscal_position_map(self, **kwargs):
        ctx = dict(self.env.context)
        if ctx.get('fiscal_category_id'):
            kwargs['fiscal_category_id'] = ctx.get('fiscal_category_id')
        ctx.update({
            'use_domain': ('use_picking', '=', True),
            'fiscal_category_id': kwargs['fiscal_category_id'],
        })
        return self.env['account.fiscal.position.rule'].with_context(
            ctx).apply_fiscal_mapping(**kwargs)

    @api.multi
    def _create_returns(self):
        """
         Creates return picking.
         @param self: The object pointer.
         @return: A dictionary which of fields with values.
        """
        context = dict(self.env.context)
        picking_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']

        origin_picking = self.env['stock.picking'].browse(
            self.env.context['active_id'])
        refund_fiscal_category = (
            origin_picking.fiscal_category_id.refund_fiscal_category_id)

        if not refund_fiscal_category:
            raise UserError(
                _('Error!'),
                _('This Fiscal Operation does not has Fiscal'
                  ' Operation for Returns!'))

        new_picking_id, pick_type_id = super(
            StockReturnPicking, self)._create_returns()

        picking = picking_obj.browse(new_picking_id)

        if self.invoice_state == '2binvoiced':

            values = {
                'fiscal_category_id': refund_fiscal_category.id,
                'fiscal_position_id': False}

            picking_partner = self.env[
                'res.partner'].browse(picking.partner_id.id)
            partner_invoice_id = picking_partner.address_get(
                ['invoice'])['invoice']
            partner_invoice = self.env[
                'res.partner'].browse(partner_invoice_id)

            kwargs = {
                'partner_id': picking.partner_id,
                'partner_invoice_id': partner_invoice,
                'partner_shipping_id': picking.partner_id,
                'company_id': picking.company_id,
                'context': context,
                'fiscal_category_id': refund_fiscal_category,
            }

            fiscal_position = self._fiscal_position_map(
                **kwargs)
            if fiscal_position:
                values['fiscal_position_id'] = fiscal_position.id

            picking.write(values)
            for move in picking.move_lines:
                line_fiscal_category = (
                    move.origin_returned_move_id.
                    fiscal_category_id.refund_fiscal_category_id)
                kwargs.update(
                    {'fiscal_category_id': line_fiscal_category})
                fiscal_position = self._fiscal_position_map(
                    **kwargs)

                line_values = {
                    'invoice_state': self.invoice_state,
                    'fiscal_category_id': line_fiscal_category.id,
                    'fiscal_position_id': fiscal_position.id,
                }
                write_move = move_obj.browse(move.id)
                write_move.write(line_values)

        return new_picking_id, pick_type_id
