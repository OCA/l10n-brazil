# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion                                    #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU Affero General Public License as published by    #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU Affero General Public License for more details.                            #
#                                                                               #
#You should have received a copy of the GNU Affero General Public License       #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

from osv import fields, osv

from tools.translate import _

class stock_invoice_onshipping(osv.osv_memory):
    
    _inherit = "stock.invoice.onshipping"

    def _get_journal_id(self, cr, uid, context=None):

        if context is None:
            context = {}

        model = context.get('active_model')
        if not model or model != 'stock.picking':
            return []

        model_pool = self.pool.get(model)
        acct_obj = self.pool.get('account.journal')
        res_ids = context and context.get('active_ids', [])
        vals=[]
        pick_types = list(set(map(lambda x: x.type, model_pool.browse(cr, uid, res_ids, context=context))))
        for type in pick_types:
            if type == 'out':
               value = acct_obj.search(cr, uid, [('type', 'in',('sale','purchase_refund') )])
               for jr_type in acct_obj.browse(cr, uid, value, context=context):
                   t1 = jr_type.id,jr_type.name
                   vals.append(t1)

            elif type == 'in':
               value = acct_obj.search(cr, uid, [('type', 'in',('purchase','sale_refund') )])
               for jr_type in acct_obj.browse(cr, uid, value, context=context):
                   t1 = jr_type.id,jr_type.name
                   vals.append(t1)
            else:
               value = acct_obj.search(cr, uid, [('type', 'in',('cash','bank','general','situation') )])
               for jr_type in acct_obj.browse(cr, uid, value, context=context):
                   t1 = jr_type.id,jr_type.name
                   vals.append(t1)
        return vals

    _columns = {
                'journal_id': fields.selection(_get_journal_id, 'Destination Journal'),
                'operation_category_journal': fields.boolean("Diário da Categoria"),
    }
    
    _defaults = {
                 'operation_category_journal': True
                 }


    def view_init(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        res = super(stock_invoice_onshipping, self).view_init(cr, uid, fields_list, context=context)
        pick_obj = self.pool.get('stock.picking')
        count = 0
        active_ids = context.get('active_ids',[])
        for pick in pick_obj.browse(cr, uid, active_ids, context=context):
            if pick.invoice_state != '2binvoiced':
                count += 1
        if len(active_ids) == 1 and count:
            raise osv.except_osv(_('Warning !'), _('This picking list does not require invoicing.'))
        if len(active_ids) == count:
            raise osv.except_osv(_('Warning !'), _('None of these picking lists require invoicing.'))
        return res

    def open_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoice_ids = []
        data_pool = self.pool.get('ir.model.data')
        res = self.create_invoice(cr, uid, ids, context=context)
        invoice_ids += res.values()
        inv_type = context.get('inv_type', False)
        action_model = False
        action = {}
        if not invoice_ids:
            raise osv.except_osv(_('Error'), _('No Invoices were created'))
        if inv_type == "out_invoice":
            action_model,action_id = data_pool.get_object_reference(cr, uid, 'account', "action_invoice_tree1")
        elif inv_type == "in_invoice":
            action_model,action_id = data_pool.get_object_reference(cr, uid, 'account', "action_invoice_tree2")
        elif inv_type == "out_refund":
            action_model,action_id = data_pool.get_object_reference(cr, uid, 'account', "action_invoice_tree3")
        elif inv_type == "in_refund":
            action_model,action_id = data_pool.get_object_reference(cr, uid, 'account', "action_invoice_tree4")
        if action_model:
            action_pool = self.pool.get(action_model)
            action = action_pool.read(cr, uid, action_id, context=context)
            action['domain'] = "[('id','in', ["+','.join(map(str,invoice_ids))+"])]"
        return action

    def create_invoice(self, cr, uid, ids, context=None):
        
        onshipdata_obj = self.read(cr, uid, ids, ['journal_id', 'group', 'invoice_date', 'operation_category_journal'])
        res = super(stock_invoice_onshipping, self).create_invoice(cr, uid,  ids, context)
        
        if not res or not onshipdata_obj[0]['operation_category_journal']:
            return res
        
        if context is None:
            context = {}
        
        for inv in self.pool.get('account.invoice').browse(cr, uid, res.values(), context=context):
            
            journal_ids = [jou for jou in inv.fiscal_operation_category_id.journal_ids if jou.company_id == inv.company_id]
            
            if not journal_ids:
                raise osv.except_osv(_('Invalid Journal !'), _('There is not journal defined for this company in fiscal operation %s !') % (fiscal_operation_category_id.name))

            self.pool.get('account.invoice').write(cr, uid, inv.id, {'journal_id': journal_ids[0].id}, context=context)
        
        return res

stock_invoice_onshipping()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
