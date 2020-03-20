# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class FiscalTax(models.Model):
    _inherit = 'l10n_br_fiscal.tax'

    @api.multi
    def _create_account_tax(self):
        for fiscal_tax in self:
            account_tax_group_id = self.env['account.tax.group'].search(
                [('fiscal_tax_group_id', '=', fiscal_tax.tax_group_id.id)],
                limit=1)

            account_taxes = self.env['account.tax'].search(
                [('tax_group_id', '=', account_tax_group_id.id)])

            if not account_taxes:

                tax_users = {'sale': 'out', 'purchase': 'in'}

                for tax_use in tax_users.keys():
                    tax_values = {
                        'name': fiscal_tax.name + ' ' + tax_users.get(tax_use),
                        'type_tax_use': tax_use,
                        'fiscal_tax_ids': [(4, fiscal_tax.id)],
                        'tax_group_id': account_tax_group_id.id,
                        'amount': 0.00
                    }

                    self.env['account.tax'].create(tax_values)

            else:
                account_taxes.write({
                    'fiscal_tax_ids': [(4, t.id) for t in account_taxes]
                })

    @api.model
    def create(self, values):
        fiscal_taxes = super(FiscalTax, self).create(values)
        fiscal_taxes._create_account_tax()
        return fiscal_taxes

    @api.multi
    def unlink(self):
        for fiscal_tax in self:
            account_tax_group_id = self.env['account.tax.group'].search(
                [('fiscal_tax_group_id', '=', fiscal_tax.tax_group_id.id)],
                limit=1)

            account_taxes = self.env['account.tax'].search(
                [('tax_group_id', '=', account_tax_group_id.id)])

            for account_tax in account_taxes:

                account_tax.fiscal_tax_ids -= fiscal_tax

                if not account_tax.fiscal_tax_ids:
                    active_datetime = fields.Datetime.to_string(
                        fields.Datetime.now())

                    account_tax.write({
                        'name': (account_tax.name +
                                 ' Inative ' + active_datetime),
                        'fiscal_tax_id': False,
                        'active': False})
        return super(FiscalTax, self).unlink()
