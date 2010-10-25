# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion                                    #
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


##############################################################################
# Cadastro de Impostos Personalizado
##############################################################################
class account_tax(osv.osv):
    _inherit = 'account.tax'
    
    _columns = {
        'tax_discount': fields.boolean('Descontar Imposto do Preço', help="Marque isso se este imposto é descontado no preço, exemplo: (ICMS, PIS e etc.)."),
    }
    
    def compute_all(self, cr, uid, taxes, price_unit, quantity, address_id=None, product=None, partner=None):
        """
        RETURN: {
                'total': 0.0,                # Total without taxes
                'total_included: 0.0,        # Total with taxes
                'total_tax_discount: 0.0,    # Total Tax Discounts
                'taxes': []                  # List of taxes, see compute for the format
            }
        """
        
        tax_obj = self.pool.get('account.tax')        
        result = super(account_tax, self).compute_all(cr, uid, taxes, price_unit, quantity, address_id, product, partner)
        totaldc = 0.0 
        for tax in result['taxes']:
            tax_brw = tax_obj.browse(cr, uid, tax['id'])
            if tax_brw.tax_discount:
                totaldc += tax['amount']
        
        return {
            'total': result['total'],
            'total_included': result['total_included'],
            'taxes': result['taxes'],
            'total_tax_discount': totaldc
        }
    
account_tax()
    
