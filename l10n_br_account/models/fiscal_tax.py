# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command, api, fields, models


class FiscalTax(models.Model):
    _inherit = "l10n_br_fiscal.tax"

    def account_taxes(
        self,
        user_type="sale",
        fiscal_operation=False,
        company=False,
        credit_map=None,
    ):
        """Return the account.tax records for these fiscal taxes.

        :param credit_map: optional dict {tax_domain: 'credit' | 'cost'}
            produced by ``document.line.mixin._get_stock_cost_tax_map()``.
            When provided, the DEDUCTIBLE variant of a tax is only used for
            domains resolved as 'credit' — e.g. a Lucro Presumido company
            must not book PIS/COFINS credits (cumulative regime), and a
            Simples Nacional company books none at all. When None (e.g. the
            fiscal operation has no product_destination configured), the
            historical behavior is kept: deductible variants for every tax
            when the operation has ``deductible_taxes``.
        """
        account_taxes = self.env["account.tax"]
        deductible_op = bool(fiscal_operation and fiscal_operation.deductible_taxes)
        for fiscal_tax in self:
            taxes = fiscal_tax._account_taxes(company)
            if (
                deductible_op
                and credit_map is not None
                and fiscal_tax.tax_domain in credit_map
            ):
                # Granularidade por imposto (resolvedor regime x destinação x
                # fornecedor — Fase F):
                # * CREDITÁVEL: variante normal (debita "a Compensar") + a
                #   dedutível (credita a conta da linha do produto) → custo
                #   líquido formado na conta certa;
                # * NÃO creditável POR DENTRO (ICMS/PIS/COFINS embutidos):
                #   nenhuma variante — o valor já está no preço e permanece
                #   no custo; o total da fatura não depende dele;
                # * NÃO creditável POR FORA (IPI): variante "s/ Crédito"
                #   (par +100/-100 sem contas → amount 0, total correto);
                #   fallback para o par histórico se a variante não existir
                #   no plano de contas (bases antigas), mantendo o balanço.
                # NF-e/SPED não dependem do account.tax (campos fiscais).
                usable = taxes.filtered(
                    lambda t: t.type_tax_use == user_type and t.active
                )
                if credit_map.get(fiscal_tax.tax_domain) == "credit":
                    account_taxes |= usable.filtered(lambda t: not t.no_credit)
                elif not fiscal_tax.tax_group_id.tax_include:
                    no_credit_taxes = usable.filtered("no_credit")
                    account_taxes |= no_credit_taxes or usable.filtered(
                        lambda t: not t.no_credit
                    )
                continue
            # Comportamento histórico (sem mapa de creditabilidade):
            # Atualiza os impostos contábeis relacionados aos impostos fiscais
            account_taxes |= taxes.filtered(
                lambda t: t.type_tax_use == user_type
                and t.active
                and not t.deductible
                and not t.no_credit
            )
            # Caso a operação fiscal esteja definida para usar o impostos
            # dedutíveis os impostos contáveis dedutíveis são adicionados na linha
            # da movimentação/fatura
            if deductible_op:
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
