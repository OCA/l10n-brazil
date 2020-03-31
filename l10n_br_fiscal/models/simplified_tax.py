# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class SimplifiedTax(models.Model):
    _name = 'l10n_br_fiscal.simplified.tax'
    _description = 'National Simplified Tax'

    name = fields.Char(
        string='Name',
        required=True)

    cnae_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.cnae',
        relation='fiscal_simplified_tax_cnae_rel',
        colunm1='company_id',
        colunm2='cnae_id',
        domain="[('internal_type', '=', 'normal')]",
        string='CNAEs')

    simplified_tax_range_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.simplified.tax.range',
        inverse_name='simplified_tax_id',
        string='Simplified Tax Range',
        copy=False)
