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
    _columns = {
                'partner_fiscal_type_id': fields.many2one('l10n_br_account.partner.fiscal.type', 'Tipo Fiscal do Parceiro'),
                'fiscal_operation_category_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria', requeried=True),
                'use_picking' : fields.boolean('Use in Picking'),
                }
    
    def fiscal_position_map(self, cr, uid, ids, partner_id=False, partner_address_id=False, company_id=False, fiscal_operation_category_id=False, set_default=True, context=None):

        my_partner_id = partner_invoice_id or partner_id

        
        if my_partner_id == False or shop_id == False:
             result['value']['fiscal_position'] = False
             result['value']['fiscal_operation_id'] = False
             return result

        # Recover involved objects --------------------------------------

        # Partner: Invoice partner priority
        Partner = self.pool.get("res.partner").browse(cr, uid, my_partner_id) or False
        
        # Shop
        Shop = self.pool.get("sale.shop").browse(cr, uid, shop_id) or False

        # Fiscal Category
        Operation = False

        if not fiscal_operation_category_id == False: 
            Operation = fiscal_operation_category_id
        else:
            Operation = False
        
        if Operation == False and set_default == True:
           Operation = Shop.default_fo_category_id.id
           result['value']['fiscal_operation_category_id'] = Shop.default_fo_category_id.id
        if not Operation == False:
            FiscalCategory = self.pool.get("l10n_br_account.fiscal.operation.category").browse(cr, uid, Operation)
        else:
            FiscalCategory = False
        
        # Fiscal data determination -------------------------------------

        #Case 0: Any object missing
        if Partner == False or Shop == False or FiscalCategory == False:
            result['value']['fiscal_position'] = False
            result['value']['fiscal_operation_id'] = False
            return
        
        #Case 1: Parnter Specific Fiscal Posigion
        if not Partner.property_account_position.id == False:
            result['value']['fiscal_position'] = Partner.property_account_position.id
            result['value']['fiscal_operation_id'] = Partner.property_account_position.id.fiscal_operation_id.id
            return
        
        #Case 2: Rule based determination
        company_addr = self.pool.get('res.partner').address_get(cr, uid, [Shop.company_id.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]
        
        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id        

        partner_addr_default = self.pool.get('res.partner.address').browse(cr, uid, Partner.id)
        to_country = partner_addr_default.country_id.id
        to_state = partner_addr_default.state_id.id
        
        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, ['&',('company_id','=', Shop.company_id.id),('use_sale','=',True),('fiscal_operation_category_id','=',FiscalCategory.id),
                                                                                    '|',('from_country','=',from_country),('from_country','=',False),
                                                                                    '|',('to_country','=',to_country),('to_country','=',False),
                                                                                    '|',('from_state','=',from_state),('from_state','=',False),
                                                                                    '|',('to_state','=',to_state),('to_state','=',False),
                                                                                    '|',('partner_fiscal_type_id','=',Partner.partner_fiscal_type_id.id),('partner_fiscal_type_id','=',False),
                                                                                    ])
        
        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            result['value']['fiscal_position'] = obj_fpo_rule.fiscal_position_id.id
            result['value']['fiscal_operation_id'] = obj_fpo_rule.fiscal_position_id.fiscal_operation_id.id
        
        return result
    
account_fiscal_position_rule()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: