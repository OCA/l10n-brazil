# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command, api, fields, models


class FiscalTax(models.Model):
    _inherit = "l10n_br_fiscal.tax"

    def account_taxes(self, user_type="sale", fiscal_operation=False, company=False):
        account_taxes = self.env["account.tax"]
        for fiscal_tax in self:
            taxes = fiscal_tax._account_taxes(company)
            # Atualiza os impostos contábeis relacionados aos impostos fiscais
            account_taxes |= taxes.filtered(
                lambda t: t.type_tax_use == user_type and t.active and not t.deductible
            )
            # Caso a operação fiscal esteja definida para usar o impostos
            # dedutíveis os impostos contáveis dedutíveis são adicionados na linha
            # da movimentação/fatura
            if fiscal_operation and fiscal_operation.deductible_taxes:
                account_taxes |= taxes.filtered(
                    lambda t: t.type_tax_use == user_type and t.active and t.deductible
                )

        return account_taxes

    def _account_taxes(self, company=False):
        self.ensure_one()
        account_tax_group = self.tax_group_id.account_tax_group()
        if not company:
            company = self.env.company
            if self.env.context.get("default_company_id") or self.env.context.get(
                "allowed_company_ids"
            ):
                company = self.env["res.company"].browse(
                    self.env.context.get("default_company_id")
                    or self.env.context.get("allowed_company_ids")[0]
                )
        return self.env["account.tax"].search(
            [
                ("tax_group_id", "=", account_tax_group.id),
                ("active", "=", True),
                ("company_id", "=", company.id),
            ]
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
                        "fiscal_tax_ids": [Command.link(fiscal_tax.id)],
                        "tax_group_id": fiscal_tax.tax_group_id.account_tax_group().id,
                        "amount": 0.00,
                    }

                    self.env["account.tax"].create(tax_values)

            else:
                account_taxes.write({"fiscal_tax_ids": [Command.link(fiscal_tax.id)]})

    @api.model_create_multi
    def create(self, vals_list):
        fiscal_taxes = super().create(vals_list)
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
