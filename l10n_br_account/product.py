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

from openerp import models, fields
from .l10n_br_account import PRODUCT_FISCAL_TYPE, PRODUCT_FISCAL_TYPE_DEFAULT


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fiscal_category_default_ids = fields.One2many(
        'l10n_br_account.product.category', 'product_tmpl_id',
        string=u'Categoria de Operação Fiscal Padrões')
    service_type_id = fields.Many2one(
        'l10n_br_account.service.type', string=u'Tipo de Serviço')
    fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE, string='Tipo Fiscal', required=True, 
        default=PRODUCT_FISCAL_TYPE_DEFAULT)


class L10n_brAccountProductFiscalCategory(models.Model):
    """ Troca a a categoria de operação padrão pela de destino:
    
        Exemplo a categoria padrão de venda é Venda de produtos de fabricação 
        propria, mas a empresa tambem revende determinados produtos, nesses 
        determinados produtos deve se colocar a categoria de troca Venda de 
        produtos de fabricação propria por Revenda, assim sera determinada 
        a CFOP correta na fatura.
    """
    _name = 'l10n_br_account.product.category'

    fiscal_category_source_id = fields.Many2one(
        'l10n_br_account.fiscal.category', string='Categoria de Origem')
    fiscal_category_destination_id = fields.Many2one(
        'l10n_br_account.fiscal.category', string='Categoria de Destino')
    product_tmpl_id = fields.Many2one(
        'product.template', string='Produto', ondelete='cascade')
