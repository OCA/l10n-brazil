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

        result = {}

        if partner_id == False or company_id == False or fiscal_operation_category_id:
             result['fiscal_position'] = False
             result['fiscal_operation_id'] = False
             result['fiscal_operation_category_id'] = False
             return result

        obj_parnter = self.pool.get("res.partner")
        obj_company = self.pool.get("res.company")
        obj_partner_address = self.pool.get("res.partner.address")

        #Partner
        parnter = obj_partner.browse(cr, uid, partner_id)
        
        if parnter.property_account_position.id:
            result['fiscal_position'] = parnter.property_account_position.id
            result['fiscal_operation_id'] = parnter.property_account_position.fiscal_operation_id and parnter.property_account_position.fiscal_operation_id.id
            result['fiscal_operation_category_id'] = parnter.property_account_position.fiscal_operation_id and parnter.property_account_position.fiscal_operation_id.fiscal_operation_category_id and parnter.property_account_position.fiscal_operation_id.fiscal_operation_category_id.id
            return result
        
        if partner_address_id:
            partner_addr_default = obj_partner_address.browse(cr, uid, partner_id)
        else:
            partner_addr = obj_partner.address_get(cr, uid, [company.partner_id.id], ['default'])
            partner_addr_default = obj_partner_address.browse(cr, uid, [company_addr['default']])[0]
        
        to_country = partner_addr_default.country_id.id
        to_state = partner_addr_default.state_id.id

        #Company
        company = obj_company.browse(cr, uid, company_id)
        company_addr = obj_partner.address_get(cr, uid, [company.partner_id.id], ['invoice','default'])
        company_addr_default = obj_partner_address.browse(cr, uid, [company_addr['invoice']])[0]
        
        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id        

        fsc_pos_id = self.search(cr, uid, ['&',('company_id','=', Shop.company_id.id),('use_sale','=',True),('fiscal_operation_category_id','=',FiscalCategory.id),
                                            '|',('from_country','=',from_country),('from_country','=',False),
                                            '|',('to_country','=',to_country),('to_country','=',False),
                                            '|',('from_state','=',from_state),('from_state','=',False),
                                            '|',('to_state','=',to_state),('to_state','=',False),
                                            '|',('partner_fiscal_type_id','=',Partner.partner_fiscal_type_id.id),('partner_fiscal_type_id','=',False),
                                            ])
        
        if fsc_pos_id:
            obj_fpo_rule = self.browse(cr, uid, fsc_pos_id)[0]
            result['fiscal_position'] = obj_fpo_rule.fiscal_position_id.id
            result['fiscal_operation_id'] = obj_fpo_rule.fiscal_position_id and obj_fpo_rule.fiscal_position_id.fiscal_operation_id.id
        
        return result
    
account_fiscal_position_rule()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: