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
from osv import fields, osv
import pooler
from tools import config
from tools.translate import _

##############################################################################
# Pedido de venda customizado
##############################################################################
class sale_order(osv.osv):
    
    _inherit = 'sale.order'
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context):
        res = super(sale_order, self)._amount_all(cr, uid, ids, field_name, arg, context)
        
        #Não é mostrado valores de impostos na ordem de venda
        for order in self.browse(cr, uid, ids):
            res[order.id]['amount_tax'] = 0
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
            
        return res

    def _get_order(self, cr, uid, ids, context={}):
        result = super(sale_order, self)._get_order(cr, uid, ids, context)
        return result.keys()

    _columns = {
                'fiscal_operation_category_id': fields.many2one('l10n_br.fiscal.operation.category', 'Categoria', requeried=True),
                'fiscal_operation_id': fields.many2one('l10n_br.fiscal.operation', 'Operação Fiscal', domain="[('fiscal_operation_category_id','=',fiscal_operation_category_id)]" ),
                'amount_untaxed': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Untaxed Amount',
                store = {
                         'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                         'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                         },
                multi='sums'),
                'amount_tax': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Taxes',
                store = {
                         'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                         'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                         },
                multi='sums'),
                'amount_total': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Total',
                store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                         'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                         },
                multi='sums'),
               }
    
    def onchange_shop_id(self, cr, uid, ids, shop_id):
        
        result = super(sale_order, self).onchange_shop_id(cr, uid, ids, shop_id)
        if shop_id:
            obj_shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
            if obj_shop.default_fo_category_id.id:
                result['value']['fiscal_operation_category_id'] = obj_shop.default_fo_category_id.id
                
        return result
    
sale_order()

##############################################################################
# Estabelecimento Customizado
##############################################################################
class sale_shop(osv.osv):
    
    _inherit = 'sale.shop'
    _columns = {
                'default_fo_category_id': fields.many2one('l10n_br.fiscal.operation.category', 'Categoria Fiscal Padrão', requeried=True),
    }

sale_shop()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: