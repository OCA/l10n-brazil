# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2013  Renato Lima - Akretion
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp import models, fields

PRODUCT_FISCAL_TYPE = [
    ('service', u'Serviço'),
    ('product', 'Produto'),
]

PRODUCT_FISCAL_TYPE_DEFAULT = PRODUCT_FISCAL_TYPE[0][0]


class L10n_brAccountFiscalCategory(models.Model):
    """Inherit class to change default value of fiscal_type field"""
    _inherit = 'l10n_br_account.fiscal.category'

    fiscal_type = fields.Selection(PRODUCT_FISCAL_TYPE,
                                   u'Tipo Fiscal',
                                   required=True,
                                   default=PRODUCT_FISCAL_TYPE_DEFAULT)


class L10n_brAccountDocumentSerie(models.Model):
    """Inherit class to change default value of fiscal_type field"""
    _inherit = 'l10n_br_account.document.serie'

    fiscal_type = fields.Selection(PRODUCT_FISCAL_TYPE,
                                   u'Tipo Fiscal',
                                   required=True,
                                   default=PRODUCT_FISCAL_TYPE_DEFAULT)
