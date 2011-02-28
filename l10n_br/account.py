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

class account_tax_code_template(osv.osv):

    _inherit = 'account.tax.code.template'
    _columns = {
        'domain':fields.char('Domain', size=32, help="This field is only used if you develop your own module allowing developers to create specific taxes in a custom domain."),
	'tax_discount': fields.boolean('Discount this Tax in Prince', help="Mark it for (ICMS, PIS e etc.)."),
        }
account_tax_code_template()

class account_tax_code(osv.osv):

    _inherit = 'account.tax.code'
    _columns = {
        'domain':fields.char('Domain', size=32, help="This field is only used if you develop your own module allowing developers to create specific taxes in a custom domain."),
	'tax_discount': fields.boolean('Discount this Tax in Prince', help="Mark it for (ICMS, PIS e etc.)."),
        }
account_tax_code()

class account_tax_template(osv.osv):
    _inherit = 'account.tax.template'
    
    def get_precision_tax():
        def change_digit_tax(cr):
            res = pooler.get_pool(cr.dbname).get('decimal.precision').precision_get(cr, 1, 'Account')
            return (16, res+2)
        return change_digit_tax
    
    _columns = {
        'tax_discount': fields.boolean('Discount this Tax in Prince', help="Mark it for (ICMS, PIS e etc.)."),
        'base_reduction': fields.float('Redution', required=True, digits_compute=get_precision_tax(), help="Um percentual decimal em % entre 0-1."),
        'amount_mva': fields.float('MVA Percent', required=True, digits_compute=get_precision_tax(), help="Um percentual decimal em % entre 0-1."),
        'type': fields.selection( [('percent','Percentage'), ('fixed','Fixed Amount'), ('none','None'), ('code','Python Code'), ('balance','Balance'), ('quantity','Quantity')], 'Tax Type', required=True,
            help="The computation method for the tax amount."),
    }
    _defaults = {
        'base_reduction': 0,
        'amount_mva': 0,
    }

account_tax_template()

class account_tax(osv.osv):
    _inherit = 'account.tax'
    
    def get_precision_tax():
        def change_digit_tax(cr):
            res = pooler.get_pool(cr.dbname).get('decimal.precision').precision_get(cr, 1, 'Account')
            return (16, res+2)
        return change_digit_tax
    
    _columns = {
        'tax_discount': fields.boolean('Discount this Tax in Prince', help="Mark it for (ICMS, PIS e etc.)."),
        'base_reduction': fields.float('Redution', required=True, digits_compute=get_precision_tax(), help="Um percentual decimal em % entre 0-1."),
        'amount_mva': fields.float('MVA Percent', required=True, digits_compute=get_precision_tax(), help="Um percentual decimal em % entre 0-1."),
        'type': fields.selection( [('percent','Percentage'), ('fixed','Fixed Amount'), ('none','None'), ('code','Python Code'), ('balance','Balance'), ('quantity','Quantity')], 'Tax Type', required=True,
            help="The computation method for the tax amount."),
    }
    _defaults = {
        'base_reduction': 0,
	'amount_mva': 0,
    }

account_tax()

class account_journal(osv.osv):
    _inherit = "account.journal"

    _columns = {
        'internal_sequence': fields.many2one('ir.sequence', 'Internal Sequence'),
    }

account_journal()
