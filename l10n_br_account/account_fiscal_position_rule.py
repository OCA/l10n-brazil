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

import time

from osv import osv, fields
import decimal_precision as dp

FISCAL_RULE_COLUMNS = {
    'partner_fiscal_type_id': fields.many2one(
        'l10n_br_account.partner.fiscal.type', 'Tipo Fiscal do Parceiro'),
    'fiscal_category_id': fields.many2one('l10n_br_account.fiscal.category',
                                          'Categoria', requeried=True),
    'fiscal_type': fields.selection(
        [('1', 'Simples Nacional'),
         ('2', 'Simples Nacional – excesso de sublimite de receita bruta'),
         ('3', 'Regime Normal')], 'Regime Tributário', required=True),
    'revenue_start': fields.float('Faturamento Inicial',
                                  digits_compute=dp.get_precision('Account'),
                                  help="Faixa inicial de faturamento bruto"),
    'revenue_end': fields.float('Faturamento Final',
                                digits_compute=dp.get_precision('Account'),
                                help="Faixa inicial de faturamento bruto")}

FISCAL_RULE_DEFAULTS = {
    'fiscal_type': '3',
    'revenue_start': 0.00,
    'revenue_end': 0.00}

class account_fiscal_position_rule_template(osv.osv):
    _inherit = 'account.fiscal.position.rule.template'
    _columns = FISCAL_RULE_COLUMNS
    _defaults = FISCAL_RULE_DEFAULTS

account_fiscal_position_rule_template()


class account_fiscal_position_rule(osv.osv):
    _inherit = 'account.fiscal.position.rule'
    _columns = FISCAL_RULE_COLUMNS
    _defaults = FISCAL_RULE_DEFAULTS

    def fiscal_position_map(self, cr, uid, partner_id=False,
        partner_invoice_id=False, company_id=False, fiscal_category_id=False,
        context=None):
        
        # Initiate variable result
        result = {'fiscal_position': False}

        if not partner_id or not company_id or not fiscal_category_id:
             return result

        obj_partner = self.pool.get("res.partner").browse(cr, uid, partner_id)
        obj_company = self.pool.get("res.company").browse(cr, uid, company_id)
        
        # Case 1: If Partner has Specific Fiscal Posigion
        if obj_partner.property_account_position.id:
            result['fiscal_position'] = obj_partner.property_account_position.id
            return result

		# Case 2: Search fiscal position using Account Fiscal Position Rule
        company_addr = self.pool.get('res.partner').address_get(
            cr, uid, [obj_company.partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(
           cr, uid, [company_addr['default']])[0]
        
        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id

        # FIXME - Este comando if repete o browse que poderia ser melhorado
        if not partner_invoice_id:
            partner_addr = self.pool.get('res.partner').address_get(
                cr, uid, [obj_partner.id], ['invoice'])
            partner_addr_default = self.pool.get('res.partner.address').browse(
                cr, uid, [partner_addr['invoice']])[0]
        else:
            partner_addr_default = self.pool.get('res.partner.address').browse(
                cr, uid, partner_invoice_id)

        to_country = partner_addr_default.id and \
            partner_addr_default.country_id.id or False
        to_state = partner_addr_default.id and \
        partner_addr_default.state_id.id or False        

        document_date = context.get('date', time.strftime('%Y-%m-%d'))

        use_domain = context.get('use_domain', ('use_sale', '=', True))

        domain = [
            '&', ('company_id', '=', company_id), 
            ('fiscal_category_id', '=', fiscal_category_id), 
            use_domain,
            ('fiscal_type', '=', obj_company.fiscal_type),
            '|', ('from_country','=',from_country),
            ('from_country', '=', False), 
            '|', ('to_country', '=', to_country), ('to_country', '=', False), 
            '|', ('from_state', '=', from_state), ('from_state', '=', False), 
            '|', ('to_state','=', to_state), ('to_state', '=', False),
            '|', ('date_start', '=', False),
            ('date_start', '<=', document_date),
            '|', ('date_end', '=', False), ('date_end', '>=', document_date),
            '|', ('revenue_start', '=', False),
            ('revenue_start', '<=', obj_company.annual_revenue),
            '|', ('revenue_end', '=', False),
            ('revenue_end', '>=', obj_company.annual_revenue)]
        
        fsc_pos_id = self.search(cr, uid, domain)
        
        if fsc_pos_id:
            obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
            result['fiscal_position'] = obj_fpo_rule.fiscal_position_id.id
        
        return result
    
    def product_fiscal_category_map(self, cr, uid, product_id=False,
                                        fiscal_category_id=False):
        result = False

        if not product_id or not fiscal_category_id:
            return result

        product_tmpl_id = self.pool.get('product.product').read(cr, uid, product_id, ['product_tmpl_id'])['product_tmpl_id'][0]
        default_product_fiscal_category = self.pool.get('l10n_br_account.product.category').search(cr, uid, [('product_tmpl_id', '=', product_tmpl_id), 
                                                                                                             ('fiscal_category_source_id', '=', fiscal_category_id)])
        if default_product_fiscal_category:
            fiscal_category_destination_id = self.pool.get('l10n_br_account.product.category').read(cr, uid,
                                                                                                              default_product_fiscal_category, 
                                                                                                              ['fiscal_category_destination_id'])[0]['fiscal_category_destination_id'][0]
            result = fiscal_category_destination_id
        return result

account_fiscal_position_rule()


class wizard_account_fiscal_position_rule(osv.osv_memory):
    _inherit = 'wizard.account.fiscal.position.rule'
    
    def action_create(self, cr, uid, ids, context=None):
        super(wizard_account_fiscal_position_rule, self).action_create(cr, uid, ids, context)

        obj_wizard = self.browse(cr, uid, ids[0])

        obj_fiscal_position = self.pool.get('account.fiscal.position')
        obj_fiscal_position_rule = self.pool.get('account.fiscal.position.rule')
        obj_fiscal_position_rule_template = self.pool.get('account.fiscal.position.rule.template')
        obj_res_partner = self.pool.get('res.partner')
        obj_res_country_state = self.pool.get('res.country.state')

        company_id = obj_wizard.company_id.id
        company_addr = obj_res_partner.address_get(cr, uid, [company_id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]

        pfr_ids = obj_fiscal_position_rule_template.search(cr, uid, [])

        for fpr_template in obj_fiscal_position_rule_template.browse(cr, uid, pfr_ids):

            from_country = fpr_template.from_country.id or False
            from_state = fpr_template.from_state.id or False
            to_country = fpr_template.to_country.id or False
            to_state = fpr_template.to_state.id or False
            partner_fiscal_type_id = fpr_template.partner_fiscal_type_id.id or False
            fiscal_category_id = fpr_template.fiscal_category_id.id or False
    
            fiscal_position_id = False
            fp_id = obj_fiscal_position.search(cr, uid, [
                                                         ('name', '=', fpr_template.fiscal_position_id.name),
                                                         ('company_id', '=', company_id)],)
            
            if fp_id:
                fiscal_position_id = fp_id[0]
            
            fprt_id = obj_fiscal_position_rule.search(cr, uid, [('name', '=', fpr_template.name),
                                                               ('company_id', '=', company_id),
                                                               ('description', '=', fpr_template.description),
                                                               ('from_country', '=', from_country),
                                                               ('from_state', '=', from_state),
                                                               ('to_country', '=', to_country),
                                                               ('to_state', '=', to_state),
                                                               ('use_sale', '=', fpr_template.use_sale),
                                                               ('use_invoice', '=', fpr_template.use_invoice),
                                                               ('use_purchase', '=', fpr_template.use_purchase),
                                                               ('use_picking', '=', fpr_template.use_picking),
                                                               ('fiscal_position_id', '=', fiscal_position_id),
                                                               ])

            if fprt_id:
                obj_fiscal_position_rule.write(cr, uid, fprt_id, {
                                                                  'partner_fiscal_type_id': partner_fiscal_type_id, 
                                                                  'fiscal_category_id': fiscal_category_id,
                                                                  'fiscal_type': fpr_template.fiscal_type,
                                                                  'revenue_start': fpr_template.revenue_start,
                                                                  'revenue_end': fpr_template.revenue_end,})           

        return {}

wizard_account_fiscal_position_rule()
