# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _
from odoo.addons.fiscal.constants.fiscal import TAX_DOMAIN


class AccountTaxAbstract(models.AbstractModel):
    _name = 'account.tax.fiscal.abstract'
    _description = 'Account Tax Fiscal Abstract'

    fiscal_tax_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Fiscal Tax')

    fiscal_tax_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Fiscal Tax')

    fiscal_cst_in_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cst',
        related='fiscal_tax_id.cst_in_id',
        string='CST Input')

    fiscal_cst_out_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cst',
        related='fiscal_tax_id.cst_out_id',
        string='CST Output')

    fiscal_tax_domain = fields.Selection(
        selection=TAX_DOMAIN,
        related='fiscal_tax_id.tax_domain',
        string='Tax Domain')

    @api.onchange('fiscal_tax_id')
    def _onchange_fiscal_tax_id(self):
        if self.fiscal_tax_id:
            self.amount = self.fiscal_tax_id.percent_amount
            self.description = self.fiscal_tax_id.name

            fiscal_type = {
                'sale': _('Out'),
                'purchase': _('In')}

            self.name = "{0} {1}".format(
                self.fiscal_tax_id.name,
                fiscal_type.get(self.type_tax_use, ''))
