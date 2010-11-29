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
import netsvc
import decimal_precision as dp
from osv import fields, osv
import pooler
from tools import config
from tools.translate import _

##############################################################################
# Pedido de venda customizado
##############################################################################
#class sale_order(osv.osv):
    
#    _inherit = 'sale.order'
    
#    def onchange_partner_id(self, cr, uid, ids, part, shop_id, fiscal_operation_category_id):

#        result = super(sale_order, self).onchange_partner_id(cr, uid, ids, part)
#        return result


#sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
