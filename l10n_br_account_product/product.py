# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
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
from openerp import SUPERUSER_ID

from .l10n_br_account_product import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_DEFAULT)

PRODUCT_ORIGIN = [
    ('0', u'0 - Nacional, exceto as indicadas nos códigos 3 a 5'),
    ('1', u'1 - Estrangeira - Importação direta, exceto a indicada no código 6'),
    ('2', u'2 - Estrangeira - Adquirida no mercado interno, exceto a indicada no código 7'),
    ('3', u'3 - Nacional, mercadoria ou bem com Conteúdo de Importação superior a  40% (quarenta por cento)'),
    ('4', u'4 - Nacional, cuja produção tenha sido feita em conformidade com os processos produtivos básicos de que tratam o Decreto-Lei nº 288/67, e as Leis nºs 8.248/91, 8.387/91, 10.176/01 e 11.484/07'),
    ('5', u'5 - Nacional, mercadoria ou bem com Conteúdo de Importação inferior ou igual a 40% (quarenta por cento)'),
    ('6', u'6 - Estrangeira - Importação direta, sem similar nacional, constante em lista de Resolução CAMEX'),
    ('7', u'7 - Estrangeira - Adquirida no mercado interno, sem similar nacional, constante em lista de Resolução CAMEX')
]


class ProductTemplate(orm.Model):
    _inherit = 'product.template'
    _columns = {
        'fiscal_type': fields.selection(PRODUCT_FISCAL_TYPE,
            'Tipo Fiscal', required=True),
        'origin': fields.selection(PRODUCT_ORIGIN, 'Origem'),
        'ncm_id': fields.many2one(
            'account.product.fiscal.classification', u'NCM'),
    }
    _defaults = {
        'fiscal_type': PRODUCT_FISCAL_TYPE_DEFAULT,
        'origin': '0'
    }

    def ncm_id_change(self, cr, uid, ids, ncm_id=False, sale_tax_ids=None,
                    purchase_tax_ids=None, context=None):
        """We eventually keep the sale and purchase taxes because those
        are not company wise in OpenERP. So if we choose a different
        fiscal position for a different company, we don't want to override
        other's companies setting"""
        if not context:
            context = {}

        if not sale_tax_ids:
            sale_tax_ids = [[6, 0, []]]

        if not purchase_tax_ids:
            purchase_tax_ids = [[6, 0, []]]

        result = {'value': {}}
        if ncm_id:
            fclass = self.pool.get('account.product.fiscal.classification')
            fiscal_classification = fclass.browse(
                cr, uid, ncm_id, context=context)

            current_company_id = self.pool.get('res.users').browse(
                cr, uid, uid).company_id.id
            to_keep_sale_tax_ids = self.pool.get('account.tax').search(
                cr, SUPERUSER_ID, [('id', 'in', sale_tax_ids[0][2]),
                    ('company_id', '!=', current_company_id)],
                        context=context)
            to_keep_purchase_tax_ids = self.pool.get('account.tax').search(
                cr, SUPERUSER_ID, [('id', 'in', purchase_tax_ids[0][2]),
                    ('company_id', '!=', current_company_id)],
                        context=context)

            result['value']['taxes_id'] = list(set(to_keep_sale_tax_ids + [x.id for x in fiscal_classification.sale_base_tax_ids]))
            result['value']['supplier_taxes_id'] = list(set(to_keep_purchase_tax_ids + [x.id for x in fiscal_classification.purchase_base_tax_ids]))
        return result


class ProductProduct(orm.Model):
    _inherit = 'product.product'

    def ncm_id_change(self, cr, uid, ids, ncm_id=False, sale_tax_ids=None,
                    purchase_tax_ids=None, context=None):
        """We eventually keep the sale and purchase taxes because those
        are not company wise in OpenERP. So if we choose a different
        fiscal position for a different company, we don't want to override
        other's companies setting"""

        product_template = self.pool.get('product.template')
        return product_template.ncm_id_change(
            cr, uid, ids, ncm_id, sale_tax_ids,
            purchase_tax_ids)
