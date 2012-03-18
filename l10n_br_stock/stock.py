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

from osv import osv, fields
from tools.translate import _

class stock_incoterms(osv.osv):
    _inherit = "stock.incoterms"
    
    _columns = {
                'freight_responsibility': fields.selection([('0','Emitente'),('1','Destinatário'),('2','Terceiros'),('9','Sem Frete')], 'Frete por Conta', required=True),
                }
    
    _defaults = {
                 'freight_responsibility': 0,
                 }
    
stock_incoterms()


class stock_picking(osv.osv):
    _inherit = "stock.picking"
    _description = "Picking List"

    _columns = {
                'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria'),
                'fiscal_operation_id': fields.many2one('l10n_br_account.fiscal.operation', 'Operação Fiscal',
                                                       domain="[('fiscal_operation_category_id','=',fiscal_operation_category_id)]"),
                'fiscal_position': fields.many2one('account.fiscal.position', 'Posição Fiscal',
                                                   domain="[('fiscal_operation_id','=',fiscal_operation_id)]"),
                }
    
    def _default_fiscal_operation_category(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)       
        return user.company_id and user.company_id.stock_fiscal_category_operation_id and user.company_id.stock_fiscal_category_operation_id.id or False
    
    _defaults = {
                'fiscal_operation_category_id': _default_fiscal_operation_category,
                }

    def _fiscal_position_map(self, cr, uid, partner_id, partner_invoice_id=False, 
                             company_id=False, fiscal_operation_category_id=False):
        obj_fiscal_position_rule = self.pool.get('account.fiscal.position.rule')
        
        result = obj_fiscal_position_rule.fiscal_position_map(cr, uid, partner_id, partner_invoice_id, 
                                                              company_id, fiscal_operation_category_id, 
                                                              context={'use_domain': ('use_picking','=',True)})
        return result

    def onchange_partner_in(self, cr, uid, context=None, partner_address_id=None,
                            company_id=False,fiscal_operation_category_id=False):
        result = super(stock_picking, self).onchange_partner_in(cr, uid, context, partner_address_id)

        if not result or not partner_address_id:
            result = {'value': {}}
        
        partner_addr = self.pool.get('res.partner.address').browse(cr, uid, partner_address_id)
        partner_id =  partner_addr.partner_id and partner_addr.partner_id.id
        fiscal_data = self._fiscal_position_map(cr, uid, partner_id, partner_address_id, company_id, fiscal_operation_category_id)
        result['value'].update(fiscal_data)
        return result

    def onchange_fiscal_operation_category_id(self, cr, uid, ids, partner_address_id, 
                                              company_id=False, fiscal_operation_category_id=False):
        result = {'value': {} }
        
        if not partner_address_id:
            return result
        
        partner_addr = self.pool.get('res.partner.address').browse(cr, uid, partner_address_id)
        partner_id =  partner_addr.partner_id and partner_addr.partner_id.id
        fiscal_data = self._fiscal_position_map(cr, uid, partner_id, partner_address_id, company_id, fiscal_operation_category_id)
        result['value'].update(fiscal_data)
        return result

    def _invoice_line_hook(self, cr, uid, move_line, invoice_line_id):
        '''Call after the creation of the invoice line'''
        fiscal_operation_id = fiscal_operation_category_id = False

        if move_line.sale_line_id:
            fiscal_operation_id = move_line.sale_line_id.fiscal_operation_id or move_line.sale_line_id.order_id.fiscal_operation_id 
            fiscal_operation_category_id = move_line.sale_line_id.fiscal_operation_category_id or move_line.sale_line_id.order_id.fiscal_operation_category_id

        if move_line.purchase_line_id:
            fiscal_operation_id = move_line.purchase_line_id.fiscal_operation_id or move_line.purchase_line_id.order_id.fiscal_operation_id 
            fiscal_operation_category_id = move_line.purchase_line_id.fiscal_operation_category_id or move_line.purchase_line_id.order_id.fiscal_operation_category_id       

        if not move_line.purchase_line_id and not move_line.sale_line_id:
            fiscal_operation_id = move_line.picking_id.fiscal_operation_id
            fiscal_operation_category_id = move_line.picking_id.fiscal_operation_category_id

        if not fiscal_operation_id:
            raise osv.except_osv(_('Movimentação sem operação fiscal !'),_("Não existe operação fiscal para uma linha de vendas relacionada ao produto %s .") % (move_line.product_id.name))

        self.pool.get('account.invoice.line').write(cr, uid, invoice_line_id, {'cfop_id': fiscal_operation_id.cfop_id.id, 'fiscal_operation_category_id': fiscal_operation_category_id.id ,'fiscal_operation_id': fiscal_operation_id.id})
        return super(stock_picking, self)._invoice_line_hook(cr, uid, move_line, invoice_line_id)

    def _invoice_hook(self, cr, uid, picking, invoice_id):
        '''Call after the creation of the invoice'''
        own_invoice = True

        if not picking.sale_id and not picking.purchase_id:
            salesman = uid

        if picking.sale_id:
            salesman = picking.sale_id.user_id.id
        
        if picking.purchase_id:
            salesman = picking.purchase_id.validator.id
            own_invoice = False

        company_id = self.pool.get('res.company').browse(cr, uid, picking.company_id.id)
        if not company_id.document_serie_product_ids:
            raise osv.except_osv(_('Nenhuma série de documento fiscal !'),_("Empresa não tem uma série de documento fiscal cadastrada: '%s', você deve informar uma série no cadastro de empresas") % (picking.company_id.name,))

        comment = ''
        if picking.fiscal_operation_id.inv_copy_note:
            comment = picking.fiscal_operation_id.note
        
        if picking.note:
            comment += ' - ' + picking.note
        
        self.pool.get('account.invoice').write(cr, uid, invoice_id, {'fiscal_operation_category_id': picking.fiscal_operation_category_id.id,
                                                                     'fiscal_operation_id': picking.fiscal_operation_id.id, 
                                                                     'fiscal_document_id': picking.fiscal_operation_id.fiscal_document_id.id, 
                                                                     'fiscal_position': picking.fiscal_position.id, 
                                                                     'document_serie_id': company_id.document_serie_product_ids[0].id, 
                                                                     'user_id': salesman,
                                                                     'comment': comment})
        return super(stock_picking, self)._invoice_hook(cr, uid, picking, invoice_id)

stock_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
