# -*- coding: utf-8 -*-
# Copyright (C) 2015  Luis Felipe Miléo - KMEE
# Copyright (C) 2016  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api

from openerp.addons.l10n_br_account.models.l10n_br_account import (
    L10nBrTaxDefinition
)


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    @api.multi
    @api.depends('product_tax_definition_line.tax_id')
    def _compute_taxes(self):
        for state in self:
            product_taxes = self.env['account.tax']
            for tax in state.product_tax_definition_line:
                product_taxes += tax.tax_id
            state.product_tax_ids = product_taxes

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
    cest_id = fields.Many2one(
        'l10n_br_account_product.cest',
        'CEST'
    )

    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq',
         'unique (tax_id, state_id)',
         u'Imposto já existente neste estado!')
    ]
