# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command, api, fields, models


class FiscalTax(models.Model):
    _inherit = "l10n_br_fiscal.tax"

    def _account_taxes_company(self, company=False):
        if company:
            return company
        # ``self.env.company`` already resolves ``allowed_company_ids[0]`` *with*
        # access validation, so it replaces the previous raw browse of that id.
        # A ``default_company_id`` in the context is still honoured as an
        # explicit override.
        company = self.env.company
        if self.env.context.get("default_company_id"):
            company = self.env["res.company"].browse(
                self.env.context["default_company_id"]
            )
        return company

    def account_taxes(self, user_type="sale", fiscal_operation=False, company=False):
        account_taxes = self.env["account.tax"]
        if not self:
            return account_taxes

        company = self._account_taxes_company(company)

        # Resolve os grupos contábeis de todos os impostos fiscais em um único
        # search e traz TODOS os account.tax dos grupos envolvidos numa única
        # query (antes: 1 search de grupo + 1 search de account.tax por imposto
        # por linha). O casamento por grupo é feito em memória.
        fiscal_group_to_account_group = self.tax_group_id._account_tax_group_map()
        account_group_ids = [
            group.id for group in fiscal_group_to_account_group.values() if group
        ]
        candidate_taxes = self.env["account.tax"].search(
            [
                ("tax_group_id", "in", account_group_ids),
                ("active", "=", True),
                ("company_id", "=", company.id),
            ]
        )
        taxes_by_account_group = {}
        for tax in candidate_taxes:
            taxes_by_account_group.setdefault(
                tax.tax_group_id.id, self.env["account.tax"]
            )
            taxes_by_account_group[tax.tax_group_id.id] |= tax

        # `deductible_taxes` is company dependent, so reading it off the record
        # as it comes answers for whatever company sits in the environment, not
        # for the one resolved above. Same correction as #4996, kept here
        # because this method is rewritten by this PR: without it, whichever of
        # the two merges last silently drops the fix.
        if fiscal_operation and company:
            fiscal_operation = fiscal_operation.with_company(company)

        for fiscal_tax in self:
            account_group = fiscal_group_to_account_group.get(
                fiscal_tax.tax_group_id.id
            )
            taxes = taxes_by_account_group.get(
                account_group.id if account_group else False,
                self.env["account.tax"],
            )
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
        company = self._account_taxes_company(company)
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
