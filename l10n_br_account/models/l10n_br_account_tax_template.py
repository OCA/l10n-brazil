# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class L10nBrAccountTaxTemplate(models.Model):
    _inherit = 'l10n_br_account.tax.template'

    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='l10n_br_fiscal_l10n_br_account_template_tax_rel',
        colunm1='l10n_br_account_tax_id',
        colunm2='fiscal_tax_id',
        string='Fiscal Taxes',
    )
