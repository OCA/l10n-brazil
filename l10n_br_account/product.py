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

from osv import osv, fields


class product_template(osv.Model):
    _inherit = 'product.template'
    _columns = {
        'fiscal_category_default_ids': fields.one2many(
            'l10n_br_account.product.category', 'product_tmpl_id',
            'Categoria de Operação Fiscal Padrões'),
        'fiscal_type': fields.selection([('product', 'Produto'),
                                         ('service', 'Serviço')],
                                        'Tipo Fiscal', requeried=True),
        'is_on_service_invoice': fields.boolean('On Service Invoice?',
                                                help="True if invoiced along "
                                                "with service"),
        'origin': fields.selection([('0', 'Nacional'),
                                    ('1', 'Internacional'),
                                    ('2', 'Inter. Adiquirido Internamente')],
                                   'Origem')
    }

    _defaults = {
        'fiscal_type': 'product',
        'is_on_service_invoice': False,
        'origin': '0'
    }


class l10n_br_account_product_fiscal_category(osv.Model):
    _name = 'l10n_br_account.product.category'
    _columns = {
        'fiscal_category_source_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            'Categoria de Origem'),
        'fiscal_category_destination_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            'Categoria de Destino'),
        'product_tmpl_id': fields.many2one('product.template', 'Produto',
                                           ondelete='cascade')
    }
