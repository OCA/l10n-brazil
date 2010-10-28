# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2010  Renato Lima - Akretion                                    #
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
import netsvc
from osv import fields, osv
import decimal_precision as dp
import pooler
from tools import config
from tools.translate import _

##############################################################################
# Fatura (Nota Fiscal) Personalizado
##############################################################################
class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    _columns = {
                'carrier_id':fields.many2one("delivery.carrier","Carrier", readonly=True, states={'draft':[('readonly',False)]}),
                'weight': fields.float('Gross weight', help="The gross weight in Kg.", readonly=True, states={'draft':[('readonly',False)]}),
                'weight_net': fields.float('Net weight', help="The net weight in Kg.", readonly=True, states={'draft':[('readonly',False)]}),
                'number_of_packages': fields.integer('Volume', readonly=True, states={'draft':[('readonly',False)]}),
                'amount_insurance': fields.float('Valor do Seguro', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft':[('readonly',False)]}),
                'amount_costs': fields.float('Outros Custos', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft':[('readonly',False)]}),
                }

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
