# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Gabriel C. Stabel                                       #
# Copyright (C) 2009 - TODAY Renato Lima - Akretion                           #
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
from .l10n_br_account import PRODUCT_FISCAL_TYPE, PRODUCT_FISCAL_TYPE_DEFAULT


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fiscal_category_default_ids = fields.One2many(
        'l10n_br_account.product.category', 'product_tmpl_id',
        u'Categoria de Operação Fiscal Padrões')
    service_type_id = fields.Many2one(
        'l10n_br_account.service.type', u'Tipo de Serviço')
    fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE, 'Tipo Fiscal', required=True,
        default=PRODUCT_FISCAL_TYPE_DEFAULT)


class L10nBrAccountProductFiscalCategory(models.Model):
    _name = 'l10n_br_account.product.category'

    fiscal_category_source_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria de Origem')
    fiscal_category_destination_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria de Destino')
    product_tmpl_id = fields.Many2one(
        'product.template', 'Produto', ondelete='cascade')
    to_state_id = fields.Many2one(
        'res.country.state', 'Estado Destino')
