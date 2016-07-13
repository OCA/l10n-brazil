# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2015  Luis Felipe Miléo - KMEE                                #
# Copyright (C) 2016  Renato Lima - Akretion                                  #
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

from openerp import models, fields, api

from openerp.addons.l10n_br_account.models.l10n_br_account import (
    L10nBrTaxDefinition
)


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    @api.one
    @api.depends('product_tax_definition_line.tax_id')
    def _compute_taxes(self):
        product_taxes = self.env['account.tax']
        for tax in self.product_tax_definition_line:
            product_taxes += tax.tax_id
        self.product_tax_ids = product_taxes

    product_tax_definition_line = fields.One2many(
        'l10n_br_tax.definition.state.product',
        'state_id',
        'Taxes Definitions'
    )
    product_tax_ids = fields.Many2many(
        'account.tax',
        string='Product Taxes',
        compute='_compute_taxes',
        store=True
    )


class L10nBrTaxDefinitionStateProduct(L10nBrTaxDefinition, models.Model):
    _name = 'l10n_br_tax.definition.state.product'

    state_id = fields.Many2one(
        'res.country.state',
        u'Estado'
    )
    fiscal_classification_id = fields.Many2one(
        'account.product.fiscal.classification',
        'Classificação Fiscal'
    )

    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq',
         'unique (tax_id, state_id)',
         u'Imposto já existente neste estado!')
    ]
