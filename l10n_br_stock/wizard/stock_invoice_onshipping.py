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

from openerp.osv import orm, fields
from openerp.tools.translate import _


class stock_invoice_onshipping(orm.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    def _get_journal_id(self, cr, uid, context=None):
        if context is None:
            context = {}

        model = context.get('active_model')
        if not model or 'stock.picking' not in model:
            return []

        model_pool = self.pool.get(model)
        journal_obj = self.pool.get('account.journal')
        res_ids = context and context.get('active_ids', [])
        vals = []
        browse_picking = model_pool.browse(cr, uid, res_ids, context=context)

        for pick in browse_picking:
            if not pick.move_lines:
                continue
            src_usage = pick.move_lines[0].location_id.usage
            dest_usage = pick.move_lines[0].location_dest_id.usage
            if pick.type == 'out' and dest_usage == 'supplier':
                journal_type = 'purchase_refund'
            elif pick.type == 'out' and dest_usage == 'customer':
                journal_type = 'sale'
            elif pick.type == 'in' and src_usage == 'supplier':
                journal_type = 'purchase'
            elif pick.type == 'in' and src_usage == 'customer':
                journal_type = 'sale_refund'
            else:
                journal_type = 'sale'

            value = journal_obj.search(
                cr, uid, [('type', '=', journal_type)])
            for jr_type in journal_obj.browse(cr, uid, value, context=context):
                t1 = jr_type.id, jr_type.name
                if t1 not in vals:
                    vals.append(t1)
        return vals

    _columns = {
        'journal_id': fields.selection(_get_journal_id, 'Destination Journal'),
        'fiscal_category_journal': fields.boolean("Diário da Categoria Fiscal")
    }
    _defaults = {
        'fiscal_category_journal': True
    }

    def create_invoice(self, cr, uid, ids, context=None):
        onshipdata_obj = self.read(
            cr, uid, ids, ['journal_id', 'group', 'invoice_date',
            'fiscal_category_journal'])
        res = super(stock_invoice_onshipping, self).create_invoice(
            cr, uid, ids, context)

        if not res or not onshipdata_obj[0]['fiscal_category_journal']:
            return res

        if context is None:
            context = {}

        for inv in self.pool.get('account.invoice').browse(
            cr, uid, res.values(), context=context):
            journal_id = inv.fiscal_category_id and \
            inv.fiscal_category_id.property_journal
            if not journal_id:
                raise orm.except_orm(
                    _('Invalid Journal!'),
                    _('There is not journal defined for this company: %s in \
                    fiscal operation: %s !') % (inv.company_id.name,
                                                inv.fiscal_category_id.name))

            self.pool.get('account.invoice').write(
                cr, uid, inv.id, {'journal_id': journal_id.id},
                context=context)
        return res
