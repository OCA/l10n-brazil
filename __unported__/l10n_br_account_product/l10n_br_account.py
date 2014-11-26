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

from .l10n_br_account_product import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_DEFAULT)


class L10n_brAccountFiscalCategory(orm.Model):
    _inherit = 'l10n_br_account.fiscal.category'
    _columns = {
        'fiscal_type': fields.selection(PRODUCT_FISCAL_TYPE,
            'Tipo Fiscal', required=True),
    }
    _defaults = {
        'fiscal_type': PRODUCT_FISCAL_TYPE_DEFAULT,
    }


class L10n_brAccountDocumentSerie(orm.Model):
    _inherit = 'l10n_br_account.document.serie'
    _columns = {
        'fiscal_type': fields.selection(
            PRODUCT_FISCAL_TYPE, 'Tipo Fiscal', required=True),
    }
    _defaults = {
        'fiscal_type': PRODUCT_FISCAL_TYPE_DEFAULT,
    }


class L10n_brAccountPartnerFiscalType(orm.Model):
    _inherit = 'l10n_br_account.partner.fiscal.type'
    _columns = {
        'icms': fields.boolean('Recupera ICMS'),
        'ipi': fields.boolean('Recupera IPI')
    }
    defaults = {
        'icms': True,
        'ipi': True
    }