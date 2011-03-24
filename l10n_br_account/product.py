# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel                 #
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

from osv import osv, fields

##############################################################################
# Produto Customizado
##############################################################################
class product_product(osv.osv):

    _inherit = 'product.product'
    _columns = {
                'fiscal_category_operation_default_ids': fields.one2many('l10n_br_account.product.operation.category', 'product_id', 'Categoria de Operação Fiscal Padrões'),
                'fiscal_type': fields.selection([('product', 'Produto'), ('service', 'Serviço')], 'Tipo Fiscal', requeried=True),
                }
    _defaults = {
                'fiscal_type': 'product',
                }

product_product()

##############################################################################
# Categorias fiscais de operações padrões por produto
##############################################################################
class l10n_br_account_product_fiscal_operation_category(osv.osv):
    _name = 'l10n_br_account.product.operation.category'
    _columns = {
                'fiscal_operation_category_source_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria de Origem'),
                'fiscal_operation_category_destination_id': fields.many2one('l10n_br_account.fiscal.operation.category', 'Categoria de Origem'),
                'product_id': fields.many2one('product.product', 'Produto', ondelete='cascade'),
                }
    
l10n_br_account_product_fiscal_operation_category()
