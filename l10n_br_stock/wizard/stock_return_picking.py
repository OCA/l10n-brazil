# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from openerp.osv import orm
from openerp.tools.translate import _


class stock_return_picking(orm.TransientModel):
    _inherit = 'stock.return.picking'

    def _fiscal_position_map(self, cr, uid, result, **kwargs):
        kwargs['context'].update({'use_domain': ('use_picking', '=', True)})
        fp_rule_obj = self.pool.get('account.fiscal.position.rule')
        return fp_rule_obj.apply_fiscal_mapping(cr, uid, result, **kwargs)

    def create_returns(self, cr, uid, ids, context=None):
        """
         Creates return picking.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: List of ids selected
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
        result = super(stock_return_picking, self).create_returns(
            cr, uid, ids, context)

        data = self.read(cr, uid, ids[0])

        if data['invoice_state'] == 'none':
            return result

        picking_obj = self.pool.get('stock.picking')
        result_domain = eval(result['domain'])
        record_ids = result_domain and result_domain[0] and result_domain[0][2]
        pickings = picking_obj.browse(cr, uid, record_ids, context=context)

        for picking in pickings:
            fc_return_id = picking.fiscal_category_id \
            and picking.fiscal_category_id.refund_fiscal_category_id \
            and picking.fiscal_category_id.refund_fiscal_category_id.id

            if not fc_return_id:
                raise orm.except_orm(
                    _('Error!'),
                    _("""This Fiscal Operation does not has Fiscal Operation
                    for Returns!"""))

            values = {
                'fiscal_category_id': fc_return_id,
                'fiscal_position': False}

            partner_invoice_id = self.pool.get('res.partner').address_get(
                cr, uid, [picking.partner_id.id], ['invoice'])['invoice']

            kwargs = {
               'partner_id': picking.partner_id.id,
               'partner_invoice_id': partner_invoice_id,
               'partner_shipping_id': picking.partner_id.id,
               'company_id': picking.company_id.id,
               'context': context,
               'fiscal_category_id': fc_return_id
            }
            values.update(self._fiscal_position_map(
                cr, uid, {'value': {}}, **kwargs).get('value'))
            picking_obj.write(cr, uid, picking.id, values)
            return result
