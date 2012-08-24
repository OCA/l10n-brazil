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


class account_journal(osv.osv):
    _inherit = 'account.journal'
    _columns = {
        'revenue_expense': fields.boolean('Gera Financeiro'),
        }

account_journal()


class account_tax(osv.osv):
    _inherit = 'account.tax'
    
    def _compute_tax(self, taxes, total_line, product_weight, product_qty, precision):
        result = {'tax_discount': 0.0, 'taxes': []}
        for tax in taxes:
            if tax.get('type') == 'weight':
                tax['amount'] = round((product_qty * product_weight) * tax['percent'], precision)
    
            if tax.get('type') == 'quantity':
                tax['amount'] = round(product_qty * tax['percent'], precision)

            if tax.get('tax_discount', False):
                result['tax_discount'] = tax['amount']

            tax['amount'] = round(tax['amount'] * (1 - tax['base_reduction']), precision)  
            tax['total_base'] = round(total_line * (1 - tax['base_reduction']), precision)
            tax['total_base_other'] = round(total_line - tax['total_base'], precision)
        
        result['taxes'] = taxes
        return result
        
    def compute_all(self, cr, uid, taxes, price_unit, quantity, address_id=None, product=None, partner=None, force_excluded=False, fiscal_operation=False):
        """
        RETURN: {
                'total': 0.0,                 # Total without taxes
                'total_included': 0.0,        # Total with taxes
                'total_tax_discount': 0.0,    # Total Tax Discounts
                'taxes': []                   # List of taxes, see compute for the format
                'total_base': 0.0,            # Total Base by tax
            }
        """
        obj_precision = self.pool.get('decimal.precision')
        precision = obj_precision.precision_get(cr, uid, 'Account')
        tax_obj = self.pool.get('account.tax')        
        result = super(account_tax, self).compute_all(cr, uid, taxes, price_unit, quantity, address_id, product, partner, force_excluded)

        totaldc = icms_base = icms_value = icms_percent = ipi_value = 0.0
        calculed_taxes = []

        for tax in result['taxes']:
            tax_list = [tx for tx in taxes if tx.id == tax['id']]
            if tax_list: tax_brw = tax_list[0]
            tax['domain'] = tax_brw.domain
            tax['type'] = tax_brw.type
            tax['percent'] = tax_brw.amount
            tax['base_reduction'] = tax_brw.base_reduction
            tax['amount_mva'] = tax_brw.amount_mva
            tax['tax_discount'] = tax_brw.base_code_id.tax_discount

        common_taxes = [tx for tx in result['taxes'] if tx['domain'] not in ['icms', 'icmsst', 'ipi']]
        result_tax = self._compute_tax(common_taxes, result['total'], product.weight_net, quantity, precision)
        totaldc += result_tax['tax_discount']
        calculed_taxes += result_tax['taxes']

        # Calcula o IPI
        specific_ipi = [tx for tx in result['taxes'] if tx['domain'] == 'ipi']
        result_ipi = self._compute_tax(specific_ipi, result['total'], product.weight_net, quantity, precision)
        totaldc += result_ipi['tax_discount']
        calculed_taxes += result_ipi['taxes']
        for ipi in result_ipi['taxes']:
            ipi_value += ipi['amount']

        # Calcula ICMS
        specific_icms = [tx for tx in result['taxes'] if tx['domain'] == 'icms']
        if fiscal_operation and fiscal_operation.asset_operation or False:
            total_base = result['total'] + ipi_value
        else:
            total_base = result['total']

        result_icms = self._compute_tax(specific_icms, result['total'], product.weight_net, quantity, precision)
        totaldc += result_icms['tax_discount']
        calculed_taxes += result_icms['taxes']
        if result_icms['taxes']:
            icms_value = result_icms['taxes'][0]['amount']
            icms_percent = result_icms['taxes'][0]['percent']
            icms_percent_reduction = result_icms['taxes'][0]['base_reduction']

        # Calcula ICMS ST
        specific_icmsst = [tx for tx in result['taxes'] if tx['domain'] == 'icmsst']
        result_icmsst = self._compute_tax(specific_icmsst, result['total'], product.weight_net, quantity, precision)
        totaldc += result_icmsst['tax_discount']
        if result_icmsst['taxes']:
            icms_st_percent = result_icmsst['taxes'][0]['percent'] or icms_percent
            icms_st_percent_reduction = result_icmsst['taxes'][0]['base_reduction'] or icms_percent_reduction
            icms_st_base = round(((result['total'] + ipi_value) * (1 + result_icmsst['taxes'][0]['amount_mva'])) * (1 - icms_st_percent_reduction), precision)
            icms_st_base_other = round(((result['total'] + ipi_value) * (1 + result_icmsst['taxes'][0]['amount_mva'])), precision) - icms_st_base
            result_icmsst['taxes'][0]['total_base'] = icms_st_base
            result_icmsst['taxes'][0]['amount'] = (icms_st_base  * icms_st_percent) - icms_value
            result_icmsst['taxes'][0]['icms_st_percent'] = icms_st_percent
            result_icmsst['taxes'][0]['icms_st_percent_reduction'] = icms_st_percent_reduction
            result_icmsst['taxes'][0]['icms_st_base_other'] = icms_st_base_other
        calculed_taxes +=result_icmsst['taxes']

        return {
            'total': result['total'],
            'total_included': result['total_included'],
            'total_tax_discount': totaldc,
            'taxes': calculed_taxes,
        }

account_tax()


class wizard_multi_charts_accounts(osv.osv_memory):
    _inherit = 'wizard.multi.charts.accounts'
    
    def execute(self, cr, uid, ids, context=None):
        res = super(wizard_multi_charts_accounts, self).execute(cr, uid, ids, context)
        
        obj_multi = self.browse(cr, uid, ids[0])
        obj_fiscal_position_template = self.pool.get('account.fiscal.position.template')
        obj_fiscal_position = self.pool.get('account.fiscal.position')

        chart_template_id = obj_multi.chart_template_id.id
        company_id = obj_multi.company_id.id
        
        fp_template_ids = obj_fiscal_position_template.search(cr, uid, [('chart_template_id', '=', chart_template_id)])
        
        for fp_template in obj_fiscal_position_template.browse(cr, uid, fp_template_ids, context=context):
            if fp_template.fiscal_operation_id:
                fp_id = obj_fiscal_position.search(cr, uid, [('name', '=', fp_template.name), ('company_id', '=', company_id)])
                if fp_id:
                    obj_fiscal_position.write(cr, uid, fp_id, {'fiscal_operation_id': fp_template.fiscal_operation_id.id})
        return res

wizard_multi_charts_accounts()

