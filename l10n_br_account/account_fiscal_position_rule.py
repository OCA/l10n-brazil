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
#GNU General Public License for more details.                                   #
#                                                                               #
#You should have received a copy of the GNU General Public License              #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

from osv import osv, fields

##############################################################################
# Modelo de Regras de Posições Fiscais Personalizadas
##############################################################################
class account_fiscal_position_rule_template(osv.osv):
    _inherit = 'account.fiscal.position.rule.template'

    _columns = {
                'partner_fiscal_type_id': fields.many2one('l10n_br_account.partner.fiscal.type', 'Tipo Fiscal do Parceiro'),
                'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria', requeried=True),
                'use_picking' : fields.boolean('Use in Picking'),
                }

account_fiscal_position_rule_template()

class account_fiscal_position_rule(osv.osv):
    _inherit = 'account.fiscal.position.rule'

    def _fiscal_position_map(self, cr, uid, partner_address_id=False, partner_invoice_id=False, partner_id=False, company_id=False, fiscal_operation_category_id=False, use_partner_default=False, context=None):
        
        # initiate result
        result = {}
        result['fiscal_position'] = False
        result['fiscal_operation_id'] = False
                     
        # Check for all needed objects ----------------------------------
        my_partner_id = partner_invoice_id or partner_id

        if my_partner_id == False or company_id == False or fiscal_operation_category_id == False:
             return result

        # Recover involved objects --------------------------------------

        # Partner: Invoice partner priority

        Partner = self.pool.get("res.partner").browse(cr, uid, my_partner_id) or False
		
        # Company
        Company = self.pool.get("res.company").browse(cr, uid, company_id) or False

        # Fiscal Category
        FiscalCategory = self.pool.get("l10n_br_account.fiscal.operation.category").browse(cr, uid, fiscal_operation_category_id) or False
		
        # Fiscal data determination -------------------------------------

        #Case 0: Any object missing
        if Partner == False or Company == False or FiscalCategory == False:
            return result
		
        #Case 1: Parnter Specific Fiscal Posigion
        if not Partner.property_account_position.id == False and use_partner_default == True:
            result['fiscal_position'] = Partner.property_account_position.id
            result['fiscal_operation_id'] = Partner.property_account_position.fiscal_operation_id.id
            return result
		
		#Case 2: Rule based determination
        company_addr = self.pool.get('res.partner').address_get(cr, uid, [Company.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]
        
        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id

        if partner_address_id == False:        
            partner_addr_default = self.pool.get('res.partner.address').browse(cr, uid, Partner.id)
        else:
            partner_addr_default = self.pool.get('res.partner.address').browse(cr, uid, partner_address_id)

        to_country = partner_addr_default.country_id.id
        to_state = partner_addr_default.state_id.id
        
        
        if context==None: 
            context = []
        
        query = ['&',('company_id','=', Company.id),
                     ('fiscal_operation_category_id','=',FiscalCategory.id), 
                    '|',('from_country','=',from_country),('from_country','=',False), 
                    '|',('to_country','=',to_country),('to_country','=',False), 
                    '|',('from_state','=',from_state),('from_state','=',False), 
                    '|',('to_state','=',to_state),('to_state','=',False), 
                    '|',('partner_fiscal_type_id','=',Partner.partner_fiscal_type_id.id),('partner_fiscal_type_id','=',False)] + context     
        
        fsc_pos_id = self.search(cr, uid, query)
        
        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            result['fiscal_position'] = obj_fpo_rule.fiscal_position_id.id
            result['fiscal_operation_id'] = obj_fpo_rule.fiscal_position_id.fiscal_operation_id.id
        
        return result
		
    def fiscal_position_map_sale(self, cr, uid, partner_invoice_id=False, partner_id=False, shop_id=False, fiscal_operation_category_id=False, set_default=True):
        
        #initiate result
        result = {}
        
        if shop_id == False:
            return result

        # Get Shop 
        Shop = self.pool.get("sale.shop").browse(cr, uid, shop_id) or False

        # Check default for fiscal_operation_category_id
        Operation = False

        if not fiscal_operation_category_id == False: 
            Operation = fiscal_operation_category_id
        
        #Set default fiscal category
        if Operation == False and set_default == True:
           Operation = Shop.default_fo_category_id.id
           result['fiscal_operation_category_id'] = Shop.default_fo_category_id.id

        result2 = self._fiscal_position_map(cr, uid, False, partner_invoice_id, partner_id, Shop.company_id.id, Operation, True, [('use_sale','=',True)])
        
        result.update(result2)
        
        return result

    def fiscal_position_map_purchase(self, cr, uid, partner_address_id=False, partner_id=False, company_id=False, fiscal_operation_category_id=False):

        result = self._fiscal_position_map(cr, uid, partner_address_id, partner_id, partner_id, company_id, fiscal_operation_category_id, False, [('use_purchase','=',True)])
        
        return result

    def fiscal_position_map_stock(self, cr, uid, partner_id=False, company_id=False, fiscal_operation_category_id=False):

        result = self._fiscal_position_map(cr, uid, partner_id, partner_id, partner_id, company_id, fiscal_operation_category_id, False, [('use_picking', '=', True)])
        
        return result

    def fiscal_position_map_invoice(self, cr, uid, partner_address_id=False, partner_invoice_id=False, partner_id=False, company_id=False, fiscal_operation_category_id=False):

        result = self._fiscal_position_map(cr, uid, partner_address_id, partner_invoice_id, partner_id, company_id, fiscal_operation_category_id, False, [('use_invoice','=',True)])
        
        return result


    _columns = {
                'partner_fiscal_type_id': fields.many2one('l10n_br_account.partner.fiscal.type', 'Tipo Fiscal do Parceiro'),
                'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria', requeried=True),
                'use_picking' : fields.boolean('Use in Picking'),
                }
    
    
account_fiscal_position_rule()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
