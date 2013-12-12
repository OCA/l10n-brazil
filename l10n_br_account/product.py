# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel               #
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

from openerp.osv import orm, fields
from .l10n_br_account import PRODUCT_FISCAL_TYPE, PRODUCT_FISCAL_TYPE_DEFAULT


class ProductTemplate(orm.Model):
    _inherit = 'product.template'
    _columns = {
        'fiscal_category_default_ids': fields.one2many(
            'l10n_br_account.product.category', 'product_tmpl_id',
            u'Categoria de Operação Fiscal Padrões'),
        'service_type_id': fields.many2one(
            'l10n_br_account.service.type', u'Tipo de Serviço'),
        'fiscal_type': fields.selection(
            PRODUCT_FISCAL_TYPE, 'Tipo Fiscal', requeried=True),
    }
    _defaults = {
        'fiscal_type': PRODUCT_FISCAL_TYPE_DEFAULT
    }


class L10n_brAccountProductFiscalCategory(orm.Model):
    _name = 'l10n_br_account.product.category'
    _columns = {
        'fiscal_category_source_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria de Origem'),
        'fiscal_category_destination_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria de Destino'),
        'product_tmpl_id': fields.many2one(
            'product.template', 'Produto', ondelete='cascade')
    }
