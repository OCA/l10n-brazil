# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp.exceptions import except_orm
from openerp import models, api, _


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def _fiscal_position_map(self, result, **kwargs):
        ctx = dict(self._context)
        ctx.update({'use_domain': ('use_picking', '=', True)})
        return self.env['account.fiscal.position.rule'].with_context(
            ctx).apply_fiscal_mapping(result, **kwargs)

    @api.multi
    def create_returns(self):
        """
         Creates return picking.
         @param self: The record set
         @return: A dictionary which of fields with values.
        """
        ctx = dict(self._context)

        picking_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        picking_type = ctx.get('default_type')

        for send_picking in picking_obj.browse(ctx.get('active_ids')):

            result = super(StockReturnPicking, self).create_returns()

            result_domain = eval(result['domain'])
            picking_ids = \
                result_domain and result_domain[0] and result_domain[0][2]

            for picking in picking_obj.browse(picking_ids):
                
                move_ids = move_obj.search([('picking_id', '=', picking.id)])

                fiscal_category_id = send_picking.fiscal_category_id \
                    and send_picking.fiscal_category_id.refund_fiscal_category_id \
                    and send_picking.fiscal_category_id.refund_fiscal_category_id.id
        
                if not fiscal_category_id:
                    raise except_orm(
                        _('Error!'),
                        _("""This Fiscal Operation does not has Fiscal Operation
                        for Returns!"""))
     
                values = {
                    'fiscal_category_id': fiscal_category_id,
                    'fiscal_position': False
                }

                partner = \
                    self.env['res.partner'].browse([picking.partner_id.id])

                partner_invoice_id = \
                    partner.address_get(['invoice'])['invoice']
     
                kwargs = {
                    'partner_id': picking.partner_id.id,
                    'partner_invoice_id': partner_invoice_id,
                    'partner_shipping_id': picking.partner_id.id,
                    'company_id': picking.company_id.id,
                    'context': ctx,
                    'fiscal_category_id': fiscal_category_id
                }
                
                values.update(self._fiscal_position_map(
                    {'value': {}}, **kwargs).get('value'))

                picking.write(values)
                               
                for idx, send_move in enumerate(send_picking.move_lines):
                    line_fiscal_category_id =  \
                        send_move.fiscal_category_id.refund_fiscal_category_id.id

                    ctx.update({
                        'parent_fiscal_category_id': line_fiscal_category_id,
                        'picking_type': picking_type,
                    })
                     
                    line_onchange = move_obj.onchange_product_id(
                        send_move.product_id.id,
                        send_move.location_id.id,
                        send_move.location_dest_id.id,
                        picking.partner_id.id)
                     
                    line_onchange['value']['fiscal_category_id'] = \
                        line_fiscal_category_id

                    for m in move_obj.browse([move_ids[idx].id]):
                        m.write(line_onchange['value'])
                     
            return result
