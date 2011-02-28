# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel                 #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU General Public License as published by           #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU General Public License for more details.                                   #
#                                                                               #
#You should have received a copy of the GNU General Public License              #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

from osv import osv, fields

##############################################################################
# Ordem de Compra Customizada
##############################################################################
class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    _columns = {
        'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria', domain="[('type','=','input'),('use_purchase','=',True)]" ),
        'fiscal_operation_id': fields.many2one('l10n_br_account.fiscal.operation', 'Operação Fiscal', domain="[('fiscal_operation_category_id','=',fiscal_operation_category_id),(type,'=','input'),('use_purchase','=',True)]" ),
    }
    
    def onchange_partner_id(self, cr, uid, ids, part, company_id=False, fiscal_operation_category_id=False):

        result = super(purchase_order, self ).onchange_partner_id(cr, uid, ids, part, company_id)

        if (not part or not company_id or not result['value']['partner_address_id'] or not fiscal_operation_category_id):
            result['value']['fiscal_position'] = False
            result['value']['fiscal_operation_id'] = False
            return result

        obj_company = self.pool.get('res.company').browse(cr, uid, [company_id])[0]

        company_addr = self.pool.get('res.partner').address_get(cr, uid, [obj_company.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]

        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id

        obj_partner = self.pool.get('res.partner').browse(cr, uid, [part])[0]
        partner_fiscal_type = obj_partner.partner_fiscal_type_id.id
        
        if obj_partner.property_account_position:
            result['value']['fiscal_position'] = obj_partner.property_account_position
            result['value']['fiscal_operation_id'] = obj_partner.property_account_position.fiscal_operation_id.id
            result['value']['fiscal_operation_category_id'] = obj_partner.property_account_position.fiscal_operation_id.fiscal_operation_category_id.id
            return result
        
        partner_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [result['value']['partner_address_id']])[0]

        to_country = partner_addr_default.country_id.id
        to_state = partner_addr_default.state_id.id

        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=',company_id), ('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_purchase','=',True),('partner_fiscal_type_id','=',partner_fiscal_type),('fiscal_operation_category_id','=',fiscal_operation_category_id)])
        if not fsc_pos_id:
            fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=',company_id), ('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_purchase','=',True),('fiscal_operation_category_id','=',fiscal_operation_category_id)])

        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            obj_fpo = self.pool.get('account.fiscal.position').browse(cr, uid, [obj_fpo_rule.fiscal_position_id.id])[0]
            obj_foperation = self.pool.get('l10n_br_account.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
            result['value']['fiscal_position'] = obj_fpo.id
            result['value']['fiscal_operation_id'] = obj_foperation.id

        return result

    def onchange_partner_address_id(self, cr, uid, ids, partner_address_id, company_id=False, fiscal_operation_category_id=False):
        
        result = super(purchase_order, self ).onchange_partner_address_id(cr, uid, ids, partner_address_id, company_id)

        if not partner_address_id or not company_id:
            result['value']['fiscal_position'] = False
            result['value']['fiscal_operation_id'] = False
            return result
        
        obj_company = self.pool.get('res.company').browse(cr, uid, [company_id])[0]

        company_addr = self.pool.get('res.partner').address_get(cr, uid, [obj_company.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]

        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id
       
        partner_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [partner_address_id])[0]

        to_country = partner_addr_default.country_id.id
        to_state = partner_addr_default.state_id.id

        obj_partner = self.pool.get('res.partner').browse(cr, uid, [partner_addr_default.partner_id.id])[0]
        partner_fiscal_type = obj_partner.partner_fiscal_type_id.id
        if obj_partner.property_account_position:
            result['value']['fiscal_position'] = obj_partner.property_account_position
            result['value']['fiscal_operation_id'] = obj_partner.property_account_position.fiscal_operation_id.id
            return result

        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=',company_id), ('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_purchase','=',True),('partner_fiscal_type_id','=',partner_fiscal_type),('fiscal_operation_category_id','=',fiscal_operation_category_id)])
        if not fsc_pos_id:
            fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=',company_id), ('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_purchase','=',True),('fiscal_operation_category_id','=',fiscal_operation_category_id)])
            
        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            obj_fpo = self.pool.get('account.fiscal.position').browse(cr, uid, [obj_fpo_rule.fiscal_position_id.id])[0]
            obj_foperation = self.pool.get('l10n_br_account.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
            result['value']['fiscal_position'] = obj_fpo.id
            result['value']['fiscal_operation_id'] = obj_foperation.id

        return result

    def onchange_fiscal_operation_category_id(self, cr, uid, ids, partner_address_id, company_id=False, fiscal_operation_category_id=False):
        
        result = {'value': {} }
        
        if not partner_address_id or not company_id or not fiscal_operation_category_id:
            result['value']['fiscal_position'] = False
            result['value']['fiscal_operation_id'] = False
            return result
        
        obj_company = self.pool.get('res.company').browse(cr, uid, [company_id])[0]

        company_addr = self.pool.get('res.partner').address_get(cr, uid, [obj_company.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]

        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id

        partner_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [partner_address_id])[0]

        to_country = partner_addr_default.country_id.id
        to_state = partner_addr_default.state_id.id

        obj_partner = self.pool.get('res.partner').browse(cr, uid, [partner_addr_default.partner_id.id])[0]
        partner_fiscal_type = obj_partner.partner_fiscal_type_id.id
        if obj_partner.property_account_position:
            result['value']['fiscal_position'] = obj_partner.property_account_position
            result['value']['fiscal_operation_id'] = obj_partner.property_account_position.fiscal_operation_id.id
            return result
        
        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=',company_id), ('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_purchase','=',True),('partner_fiscal_type_id','=',partner_fiscal_type),('fiscal_operation_category_id','=',fiscal_operation_category_id)])
        
        if not fsc_pos_id:
            fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('company_id','=',company_id), ('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_purchase','=',True),('fiscal_operation_category_id','=',fiscal_operation_category_id)])
        
        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            obj_fpo = self.pool.get('account.fiscal.position').browse(cr, uid, [obj_fpo_rule.fiscal_position_id.id])[0]
            obj_foperation = self.pool.get('l10n_br_account.fiscal.operation').browse(cr, uid, [obj_fpo.fiscal_operation_id.id])[0]
            result['value']['fiscal_position'] = obj_fpo.id
            result['value']['fiscal_operation_id'] = obj_foperation.id
            
        return result
    
    def action_invoice_create(self, cr, uid, ids, *args):
        
        res = super(purchase_order, self).action_invoice_create(cr, uid, ids, *args)

        if not res: 
            return res
        
        for order in self.browse(cr, uid, ids):
            for order_line in order.order_line: 
                for inv_line in order_line.invoice_lines: 
                
                    invoice_id = inv_line.invoice_id
                    
                    fiscal_operation_id = order_line.fiscal_operation_id or order.fiscal_operation_id 
                    fiscal_operation_category_id = order_line.fiscal_operation_category_id or order.fiscal_operation_category_id

                    if invoice_id == inv_line.invoice_id:
                        for invoice in order.invoice_ids:
                        
                            if invoice.state in ('draft'):
                                company_id = self.pool.get('res.company').browse(cr, uid,order.company_id.id)
                                if not company_id.document_serie_product_ids:
                                    raise osv.except_osv(_('No fiscal document serie found !'),_("No fiscal document serie found for selected company %s and fiscal operation: '%s'") % (order.company_id.name, order.fiscal_operation_id.code))
                                comment = ''
                                if picking.fiscal_operation_id.inv_copy_note:
                                    comment = picking.fiscal_operation_id.note
                                self.pool.get('account.invoice').write(cr, uid, invoice_id.id, {'fiscal_operation_category_id': fiscal_operation_category_id.id, 
                                                                                                'fiscal_operation_id': order.fiscal_operation_id, 
                                                                                                'cfop_id': order.fiscal_operation_id.cfop_id.id, 
                                                                                                'fiscal_document_id': fiscal_operation_id.fiscal_document_id.id, 
                                                                                                'document_serie_id': company_id.document_serie_product_ids[0].id, 
                                                                                                'own_invoice': False,
                                                                                                'comment': comment})

                            invoice_id = inv_line.invoice_id
                    
                    
                    self.pool.get('account.invoice.line').write(cr, uid, inv_line.id, {
                                                                                       'fiscal_operation_category_id': fiscal_operation_category_id.id, 
                                                                                       'fiscal_operation_id': fiscal_operation_id.id, 
                                                                                       'cfop_id': fiscal_operation_id.cfop_id.id})   
                    
        return res
        
        
        for order in self.browse(cr, uid, ids):
            for invoice in order.invoice_ids:
                if invoice.state in ('draft') and order.fiscal_operation_id:
                    #doc_serie_id = self.pool.get('l10n_br_account.document.serie').search(cr, uid,[('fiscal_document_id','=', order.fiscal_operation_id.fiscal_document_id.id),('active','=',True),('company_id','=',order.company_id.id)])
                    #if not doc_serie_id:
                    #    raise osv.except_osv(_('Nenhuma série de documento fiscal !'),_("Não existe nenhuma série de documento fiscal cadastrada para empresa:  '%s'") % (order.company_id.name,))
                    self.pool.get('account.invoice').write(cr, uid, invoice.id, {'fiscal_operation_category_id': order.fiscal_operation_category_id.id, 'fiscal_operation_id': order.fiscal_operation_id.id, 'cfop_id': order.fiscal_operation_id.cfop_id.id, 'fiscal_document_id': order.fiscal_operation_id.fiscal_document_id.id, 'fiscal_position': order.fiscal_position.id})
                    for inv_line in invoice.invoice_line:
                        self.pool.get('account.invoice.line').write(cr, uid, inv_line.id, {'cfop_id': order.fiscal_operation_id.cfop_id.id})

        return res
    
    def action_picking_create(self,cr, uid, ids, *args):

        picking_id = False

        for order in self.browse(cr, uid, ids):

            picking_id = super(purchase_order, self).action_picking_create(cr, uid, ids, *args)
            self.pool.get('stock.picking').write(cr, uid, picking_id, {'fiscal_operation_category_id': order.fiscal_operation_category_id.id, 'fiscal_operation_id': order.fiscal_operation_id.id, 'fiscal_position': order.fiscal_position.id})
        
        return picking_id
    
purchase_order()


##############################################################################
# Linhas da Ordem de Compra Customizada
##############################################################################
class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    _columns = {
        'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria', domain="[('type','=','input'),('use_purchase','=',True)]"),
        'fiscal_operation_id': fields.many2one('l10n_br_account.fiscal.operation', 'Operação Fiscal', domain="[('fiscal_operation_category_id','=',fiscal_operation_category_id),('type','=','input'),('use_purchase','=',True)]" ),
    }
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty, uom,
            partner_id, date_order=False, fiscal_position=False, date_planned=False,
            name=False, price_unit=False, notes=False,fiscal_operation_category_id=False, fiscal_operation_id=False):
        
        result = super(purchase_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom,
            partner_id, date_order, fiscal_position, date_planned, name, price_unit, notes)

        if fiscal_operation_category_id:
            result['value']['fiscal_operation_category_id'] = fiscal_operation_category_id
            
        if fiscal_operation_id:
            result['value']['fiscal_operation_id'] = fiscal_operation_id

        return result
    
purchase_order_line()