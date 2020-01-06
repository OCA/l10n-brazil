# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class FiscalTax(models.Model):
    _inherit = "l10n_br_fiscal.tax"

    @api.multi
    def _create_account_tax(self):
        for tax in self:
            account_tax_group_id = self.env["account.tax.group"].search(
                [("fiscal_tax_group_id", "=", tax.tax_group_id.id)], limit=1)

            tax_users = {"sale": "out", "purchase": "in"}

            for tax_use in tax_users.keys():
                tax_values = {
                    'name': tax.name + ' ' + tax_users.get(tax_use),
                    'type_tax_use': tax_use,
                    'fiscal_tax_id': tax.id,
                    'tax_group_id': account_tax_group_id.id
                }

                if tax.tax_base_type == 'percent':
                    type_amount = 'percent'
                    tax_amount = tax.percent_amount
                else:
                    type_amount = 'fixed'
                    tax_amount = tax.value_amount

                tax_values['tax_base_type'] = tax_amount
                tax_values['amount_type'] = type_amount

                account_tax = self.env['account.tax'].create(tax_values)
                account_tax._onchange_fiscal_tax_id()

    @api.model
    def create(self, values):
        if not values.get("partner_id"):
            self.clear_caches()

        fiscal_taxes = super(FiscalTax, self).create(values)
        fiscal_taxes._create_account_tax()
        return fiscal_taxes

    @api.multi
    def unlink(self):
        account_taxes = self.env['account.tax'].search(
            [('fiscal_tax_id', '=', self.ids)])
        active_datetime = fields.Datetime.to_string(fields.Datetime.now())

        for tax in account_taxes:
            tax.write({
                'name': tax.name + ' Inative ' + active_datetime,
                'fiscal_tax_id': False,
                'active': False})
        return super(FiscalTax, self).unlink()
