# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2009  Renato Lima - Akretion
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp import models, api, _
from openerp.exceptions import Warning as UserError


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.model
    def _fiscal_position_map(self, result, **kwargs):
        ctx = dict(self.env.context)
        if ctx.get('fiscal_category_id'):
            kwargs['fiscal_category_id'] = ctx.get('fiscal_category_id')
        ctx.update({'use_domain': ('use_picking', '=', True)})
        return self.env['account.fiscal.position.rule'].with_context(
            ctx).apply_fiscal_mapping(result, **kwargs)

    @api.multi
    def create_returns(self):
        """
         Creates return picking.
         @param self: The object pointer.
         @return: A dictionary which of fields with values.
        """
        context = dict(self.env.context)
        picking_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        for send_picking in picking_obj.browse(context.get('active_id')):

            result = super(StockReturnPicking, self).create_returns()

            result_domain = eval(result['domain'])
            picking_ids = result_domain and result_domain[0] and \
                result_domain[0][2]

            for picking in picking_obj.browse(picking_ids):

                fiscal_category_id = (send_picking.fiscal_category_id.
                                      refund_fiscal_category_id.id)

                if not fiscal_category_id:
                    raise UserError(
                        _('Error!'),
                        _('This Fiscal Operation does not has Fiscal Operation'
                          'for Returns!'))

                values = {
                    'fiscal_category_id': fiscal_category_id,
                    'fiscal_position': False}

                partner_invoice_id = self.pool.get('res.partner').address_get(
                    self._cr, self._uid, [picking.partner_id.id],
                    ['invoice'])['invoice']

                kwargs = {
                    'partner_id': picking.partner_id.id,
                    'partner_invoice_id': partner_invoice_id,
                    'partner_shipping_id': picking.partner_id.id,
                    'company_id': picking.company_id.id,
                    'context': context,
                    'fiscal_category_id': fiscal_category_id
                }

                values.update(self._fiscal_position_map(
                    {'value': {}}, **kwargs).get('value'))

                picking.write(values)
                for move in picking.move_lines:

                    line_fiscal_category_id = (
                        move.origin_returned_move_id.
                        fiscal_category_id.refund_fiscal_category_id.id)
                    kwargs.update(
                        {'fiscal_category_id': line_fiscal_category_id})

                    self._fiscal_position_map(
                        {'value': {}}, **kwargs).get('value')

                    line_values = {
                        'invoice_state': self.invoice_state,
                        'fiscal_category_id': line_fiscal_category_id,
                    }
                    line_values.update(self._fiscal_position_map(
                        {'value': {}}, **kwargs).get('value'))
                    write_move = move_obj.browse(move.id)
                    write_move.write(line_values)

            return result
