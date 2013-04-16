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


class product_template(orm.Model):
    _inherit = 'product.template'
    _columns = {
        'fiscal_category_default_ids': fields.one2many(
            'l10n_br_account.product.category', 'product_tmpl_id',
            u'Categoria de Operação Fiscal Padrões'),
        'fiscal_type': fields.selection(
            [('product', 'Produto'), ('service', 'Serviço')],
            'Tipo Fiscal', requeried=True),
        'is_on_service_invoice': fields.boolean(
            'On Service Invoice?', help="True if invoiced along with service"),
        'origin': fields.selection(
            [('0', u'0 - Nacional, exceto as indicadas nos códigos 3 a 5'),
            ('1', u'1 - Estrangeira - Importação direta, exceto a indicada no código 6'),
            ('2', u'2 - Estrangeira - Adquirida no mercado interno, exceto a indicada no código 7'),
            ('3', u'3 - Nacional, mercadoria ou bem com Conteúdo de Importação superior a  40% (quarenta por cento)'),
            ('4', u'4 - Nacional, cuja produção tenha sido feita em conformidade com os processos produtivos básicos de que tratam o Decreto-Lei nº 288/67, e as Leis nºs 8.248/91, 8.387/91, 10.176/01 e 11.484/07'),
            ('5', u'5 - Nacional, mercadoria ou bem com Conteúdo de Importação inferior ou igual a 40% (quarenta por cento)'),
            ('6', u'6 - Estrangeira - Importação direta, sem similar nacional, constante em lista de Resolução CAMEX'),
            ('7', u'7 - Estrangeira - Adquirida no mercado interno, sem similar nacional, constante em lista de Resolução CAMEX')],
            'Origem'),
        'service_type_id': fields.many2one(
            'l10n_br_account.service.type', u'Tipo de Serviço'),
    }
    _defaults = {
        'fiscal_type': 'product',
        'is_on_service_invoice': False,
        'origin': '0'
    }


class l10n_br_account_product_fiscal_category(orm.Model):
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
