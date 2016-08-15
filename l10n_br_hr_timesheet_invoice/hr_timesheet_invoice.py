# -*- coding: utf-8 -*-
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp.osv import osv


class AccountAnalyticLine(osv.osv):
    _inherit = 'account.analytic.line'

    def invoice_cost_create(self, cr, uid, ids, data=None, context=None):
        
        inv_obj = self.pool.get('account.invoice')
        line_obj = self.pool.get('account.invoice.line')
        
        context.update({'type': 'out_invoice'})
        
        invoice_ids = super(AccountAnalyticLine, self).invoice_cost_create( cr, uid, ids, data, context)
        
        for invoice in inv_obj.browse(cr, uid, invoice_ids, context=context):         

            line_ids = line_obj.search(cr, uid, [('invoice_id', '=', invoice.id)])

            if invoice.payment_term:
                payment_term = invoice.payment_term.id
            else:
                payment_term = False
            if invoice.partner_bank_id:
                bank = invoice.partner_bank_id.id
            else:
                bank = False
                
            if invoice.fiscal_category_id:
                fiscal_category_id = invoice.fiscal_category_id.id
            else:
                fiscal_category_id = False    
                
            onchange = inv_obj.onchange_partner_id(cr, uid, [invoice.id], 'out_invoice', invoice.partner_id.id, invoice.date_invoice, payment_term, bank, invoice.company_id.id, fiscal_category_id)
         
            parent_fposition_id = onchange['value']['fiscal_position']
            
            for line in invoice.invoice_line:
            
                result = line_obj.product_id_change(cr, uid, ids, line.product_id.id, line.uos_id.id, line.quantity, line.name,
                          'out_invoice', invoice.partner_id.id,
                          fposition_id=False, price_unit=line.price_unit,
                          currency_id=invoice.currency_id.id, context=context, company_id=invoice.company_id.id,
                          parent_fiscal_category_id=fiscal_category_id,
                          parent_fposition_id=parent_fposition_id)
                
                line_obj.write(cr, uid, [line.id],result['value'],context)
            inv_obj.write(cr, uid, [invoice.id], onchange['value'], context=context)
        return invoice_ids