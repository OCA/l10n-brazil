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

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from operator import itemgetter

import netsvc
import pooler
from osv import fields, osv
import decimal_precision as dp
from tools.misc import currency
from tools.translate import _
from tools import config

class account_journal(osv.osv):
    
    _inherit = 'account.journal'
    
    _columns = {
                'revenue_expense' : fields.boolean('Gera Financeiro'),
                }

account_journal()

class account_tax(osv.osv):
    _inherit = 'account.tax'
    
    def compute_all(self, cr, uid, taxes, price_unit, quantity, address_id=None, product=None, partner=None):
        """
        RETURN: {
                'total': 0.0,                 # Total without taxes
                'total_included': 0.0,        # Total with taxes
                'total_tax_discount': 0.0,    # Total Tax Discounts
                'taxes': []                   # List of taxes, see compute for the format
                        'total_base': 0.0,            # Total Base by tax
            }
        """
        
        tax_obj = self.pool.get('account.tax')        
        result = super(account_tax, self).compute_all(cr, uid, taxes, price_unit, quantity, address_id, product, partner)
        totaldc = 0.0 
        totalbr = 0.0
        obj_precision = self.pool.get('decimal.precision')
        prec = obj_precision.precision_get(cr, uid, 'Account')
        
        icms_base = 0
        icms_value = 0
        icms_percent = 0
        ipi_base = 0
        ipi_value = 0
        ipi_percent = 0
        
        for tax in result['taxes']:
            tax_brw = tax_obj.browse(cr, uid, tax['id'])
            
            if tax_brw.type == 'quantity':
                tax['amount'] = round((quantity * product.weight_net) * tax_brw.amount, prec)
            
            if tax_brw.base_code_id.tax_discount:
            
                if tax_brw.base_reduction <> 0:
                    tax['amount'] = round(tax['amount'] * (1 - tax_brw.base_reduction), prec)    

                totaldc += tax['amount']
            
            if tax_brw.amount <> 0:
                tax['total_base'] = round(result['total'] * (1 - tax_brw.base_reduction), prec)
            else:
                tax['total_base'] = 0
            
            #Guarda o valor do icms para ser usado para calcular a st 
            if tax_brw.domain == 'icms':
                icms_base = tax['total_base']
                icms_value = tax['amount']
                icms_percent = tax_brw.amount
            
            #Guarda o valor do ipi para ser usado para calcular a st 
            if tax_brw.domain == 'ipi':
                ipi_base = tax['total_base']
                ipi_value = tax['amount']
                ipi_percent = tax_brw.amount

            
        for tax_sub in result['taxes']:
            tax_brw_sub = tax_obj.browse(cr, uid, tax_sub['id'])
            if tax_brw_sub.domain == 'icmsst':
                tax_sub['total_base'] += (result['total'] + ipi_value) * (1 + tax_brw_sub.amount_mva)
                tax_sub['amount'] += (((result['total'] + ipi_value)  * (1 + tax_brw_sub.amount_mva)) * icms_percent) - icms_value 

        return {
            'total': result['total'],
            'total_included': result['total_included'],
            'total_tax_discount': totaldc,
            'taxes': result['taxes'],
        }
        
account_tax()

class wizard_multi_charts_accounts(osv.osv_memory):

    _inherit = 'wizard.multi.charts.accounts'
    
    def execute(self, cr, uid, ids, context=None):
        
        super(wizard_multi_charts_accounts, self).execute(cr, uid, ids, context)
        
        obj_multi = self.browse(cr, uid, ids[0])
        obj_fiscal_position_template = self.pool.get('account.fiscal.position.template')
        obj_fiscal_position = self.pool.get('account.fiscal.position')

        chart_template_id = obj_multi.chart_template_id.id
        company_id = obj_multi.company_id.id
        
        fp_template_ids = obj_fiscal_position_template.search(cr, uid, [('chart_template_id', '=', chart_template_id)])
        
        for fp_template in obj_fiscal_position_template.browse(cr, uid, fp_template_ids, context=context):
            if fp_template.fiscal_operation_id:
                fp_id = obj_fiscal_position.search(cr, uid, [('name','=',fp_template.name),('company_id','=',company_id)])
                if fp_id:
                    obj_fiscal_position.write(cr, uid, fp_id, {'fiscal_operation_id': fp_template.fiscal_operation_id.id})

wizard_multi_charts_accounts()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
