# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp import models, fields

from .l10n_br_account_product import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_DEFAULT)

PRODUCT_ORIGIN = [
    ('0', u'0 - Nacional, exceto as indicadas nos códigos 3 a 5'),
    ('1', u'1 - Estrangeira - Importação direta, exceto a indicada no código'
     ' 6'),
    ('2', u'2 - Estrangeira - Adquirida no mercado interno, exceto a indicada'
     u' no código 7'),
    ('3', u'3 - Nacional, mercadoria ou bem com Conteúdo de Importação'
     ' superior a 40% (quarenta por cento)'),
    ('4', u'4 - Nacional, cuja produção tenha sido feita em conformidade com'
     u' os processos produtivos básicos de que tratam o Decreto-Lei nº 288/67,'
     u' e as Leis nºs 8.248/91, 8.387/91, 10.176/01 e 11.484/07'),
    ('5', u'5 - Nacional, mercadoria ou bem com Conteúdo de Importação'
     u' inferior ou igual a 40% (quarenta por cento)'),
    ('6', u'6 - Estrangeira - Importação direta, sem similar nacional,'
     u' constante em lista de Resolução CAMEX'),
    ('7', u'7 - Estrangeira - Adquirida no mercado interno, sem similar'
     u' nacional, constante em lista de Resolução CAMEX'),
    ('8', u'8 - Nacional, mercadoria ou bem com Conteúdo de Importação'
     u' superior a 70%')
]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fiscal_type = fields.Selection(
        selection_add=PRODUCT_FISCAL_TYPE,
        default=PRODUCT_FISCAL_TYPE_DEFAULT)

    origin = fields.Selection(PRODUCT_ORIGIN, 'Origem', default='0')

    fci = fields.Char('FCI do Produto', size=36)

    service_type_id = fields.Many2one(
        'l10n_br_account.service.type', u'Tipo de Serviço')
