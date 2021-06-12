# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class FiscalTax(models.Model):
    _inherit = "l10n_br_fiscal.tax"

    def account_taxes(self, user_type="sale"):
        account_taxes = self.env["account.tax"]
        for fiscal_tax in self:
            taxes = fiscal_tax._account_taxes()
            account_taxes |= taxes.filtered(
                lambda t: t.type_tax_use == user_type and t.active
            )
        return account_taxes

    def _account_taxes(self):
        self.ensure_one()
        account_tax_group = self.tax_group_id.account_tax_group()
        return self.env["account.tax"].search(
            [("tax_group_id", "=", account_tax_group.id), ("active", "=", True)]
        )

    def _create_account_tax(self):
        for fiscal_tax in self:
            account_taxes = fiscal_tax._account_taxes()
            if not account_taxes:
                tax_users = {"sale": "out", "purchase": "in"}

                for tax_use in tax_users.keys():
                    tax_values = {
                        "name": fiscal_tax.name + " " + tax_users.get(tax_use),
                        "type_tax_use": tax_use,
                        "fiscal_tax_ids": [(4, fiscal_tax.id)],
                        "tax_group_id": fiscal_tax.account_tax_group().id,
                        "amount": 0.00,
                    }

                    self.env["account.tax"].create(tax_values)

            else:
                account_taxes.write(
                    {"fiscal_tax_ids": [(4, t.id) for t in account_taxes]}
                )

    @api.model
    def create(self, values):
        fiscal_taxes = super().create(values)
        fiscal_taxes._create_account_tax()
        return fiscal_taxes

    def unlink(self):
        for fiscal_tax in self:
            account_taxes = fiscal_tax._account_taxes()
            for account_tax in account_taxes:
                account_tax.fiscal_tax_ids -= fiscal_tax

                if not account_tax.fiscal_tax_ids:
                    active_datetime = fields.Datetime.to_string(fields.Datetime.now())

                    account_tax.write(
                        {
                            "name": (account_tax.name + " Inative " + active_datetime),
                            "fiscal_tax_ids": False,
                            "active": False,
                        }
                    )
        return super().unlink()
