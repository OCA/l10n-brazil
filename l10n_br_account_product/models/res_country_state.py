# -*- coding: utf-8 -*-
# Copyright (C) 2015  Luis Felipe Miléo - KMEE
# Copyright (C) 2016  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from .l10n_br_tax_definition_company_product import (
    L10nBrTaxDefinitionCompanyProduct
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
        comodel_name='l10n_br_tax.definition.state.product',
        inverse_name='state_id',
        string=u'Taxes Definitions')

    product_tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string=u'Product Taxes',
        compute='_compute_taxes',
        store=True)


class L10nBrTaxDefinitionStateProduct(L10nBrTaxDefinitionCompanyProduct,
                                      models.Model):
    _name = 'l10n_br_tax.definition.state.product'

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string=u'Estado')

    fiscal_classification_id = fields.Many2one(
        comodel_name='account.product.fiscal.classification',
        string=u'Classificação Fiscal')

    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq',
         'unique (tax_id, state_id)',
         u'Imposto já existente neste estado!')]
