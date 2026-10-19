# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models

ACC_NAMES = {
    "sale": {
        "account_id": "account_id",
        "refund_account_id": "refund_account_id",
    },
    "purchase": {
        "account_id": "refund_account_id",
        "refund_account_id": "account_id",
    },
    "all": {
        "account_id": "account_id",
        "refund_account_id": "refund_account_id",
    },
}


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    @api.model
    def _prepare_transfer_account_template(self, prefix=None):
        """A conta de transferência nasce classificada e com nome em português.

        Ela não é declarada pelo plano: o core a cria sozinho ao carregar a
        escrituração, procurando o primeiro código livre depois do
        `transfer_account_code_prefix`. Declará-la no plano não substitui a do
        core, faz o core criar uma SEGUNDA ao lado, porque ele desiste do
        código que já encontrou ocupado.

        O ajuste tem que ser aqui, então. Sem a classificação a conta fica de
        fora dos relatórios contábeis, que selecionam por etiqueta, e uma
        transferência entre bancos ainda em trânsito no fim do período apareceria
        como diferença sem explicação no Balanço e na demonstração dos fluxos de
        caixa. Ela é caixa e equivalentes: é conta de passagem entre duas contas
        de liquidez.
        """
        vals = super()._prepare_transfer_account_template(prefix=prefix)
        tag = self.env.ref(
            "l10n_br_coa.account_tag_cash_and_equivalents", raise_if_not_found=False
        )
        if tag:
            vals["name"] = _("Transferência entre Contas de Liquidez")
            vals["tag_ids"] = [(4, tag.id)]
        return vals

    def _prepare_all_journals(self, acc_template_ref, company, journals_dict=None):
        self.ensure_one()
        journal_data = []
        if not self.id == self.env.ref("l10n_br_coa.l10n_br_coa_template").id:
            journal_data = super()._prepare_all_journals(
                acc_template_ref, company, journals_dict
            )
        return journal_data

    def _load(self, company):
        self.ensure_one()
        result = super()._load(company)
        # Remove Company default taxes configuration
        if self.currency_id == self.env.ref("base.BRL"):
            self.env.company.write(
                {
                    "account_sale_tax_id": False,
                    "account_purchase_tax_id": False,
                }
            )
        return result

    def _load_template(
        self, company, code_digits=None, account_ref=None, taxes_ref=None
    ):
        self.ensure_one()
        account_ref, taxes_ref = super()._load_template(
            company, code_digits, account_ref, taxes_ref
        )

        if self.parent_id.id == self.env.ref("l10n_br_coa.l10n_br_coa_template").id:
            self.generate_journals(account_ref, company)

        if self.parent_id and self.parent_id == self.env.ref(
            "l10n_br_coa.l10n_br_coa_template"
        ):
            # for some reason, account_ref keys can be either account ids
            # either account records. In order to match them later we ensure
            # here keys are ids:
            account_ref = {
                k.id if hasattr(k, "id") else k: v for k, v in account_ref.items()
            }

            for tax in taxes_ref.values():
                domain = [
                    ("tax_group_id", "=", tax.tax_group_id.id),
                    ("chart_template_id", "=", self.id),
                ]
                group_tax_account_template = self.env[
                    "l10n_br_coa.account.tax.group.account.template"
                ].search(domain)
                if group_tax_account_template:
                    account, refund_account = self._get_tax_group_accounts(
                        tax, group_tax_account_template
                    )

                    account_id = account_ref[account.id].id if account else False
                    refund_account_id = (
                        account_ref[refund_account.id].id if refund_account else False
                    )
                    tax._update_repartition_lines(account_id, refund_account_id)

        return account_ref, taxes_ref

    @api.model
    def _complete_icms_st(self):
        """Give the companies that loaded the chart the ICMS ST of the sale pair.

        Taxes and accounts reach a company when the chart is loaded into it.
        A company that loaded the chart before the deductible ICMS ST existed
        has neither the tax nor the accounts of the ST group, and updating the
        module only updates the templates. This creates the missing tax from
        its template and writes the accounts of the group, on that tax and on
        the ICMS ST of the sale, as the load does. It never overwrites an
        account already there and it is safe to run more than once.
        """
        template = self.env.ref(
            "l10n_br_coa.tax_template_icms_st_out_deductible", raise_if_not_found=False
        )
        group = self.env.ref("l10n_br_coa.tax_group_icmsst", raise_if_not_found=False)
        if not template or not group:
            return
        for company in self.env["res.company"].search([]):
            base_tax = self.env.ref(
                f"l10n_br_coa.{company.id}_tax_template_out_icms_subist",
                raise_if_not_found=False,
            )
            if not base_tax or not base_tax.exists():
                continue
            tax = self.env.ref(
                f"l10n_br_coa.{company.id}_tax_template_icms_st_out_deductible",
                raise_if_not_found=False,
            )
            if not tax or not tax.exists():
                tax = template._generate_tax(company)["tax_template_to_tax"][template]
            group_account = self.env[
                "l10n_br_coa.account.tax.group.account.template"
            ].search(
                [
                    ("tax_group_id", "=", group.id),
                    ("chart_template_id", "=", company.chart_template_id.id),
                ],
                limit=1,
            )
            if not group_account:
                continue
            for item in base_tax | tax:
                line = item.invoice_repartition_line_ids.filtered(
                    lambda rl: rl.repartition_type == "tax"
                )
                if line.account_id:
                    continue
                account, refund_account = self._get_tax_group_accounts(
                    item, group_account
                )
                item._update_repartition_lines(
                    self._company_account_id(account, company),
                    self._company_account_id(refund_account, company),
                )

    @api.model
    def _company_account_id(self, account_template, company):
        """Id of the account a company got from an account template, or False."""
        if not account_template:
            return False
        xmlid = account_template.get_external_id().get(account_template.id)
        if not xmlid:
            return False
        module, name = xmlid.split(".", 1)
        account = self.env.ref(
            f"{module}.{company.id}_{name}", raise_if_not_found=False
        )
        return account.id if account and account.exists() else False

    @api.model
    def _get_tax_group_accounts(self, tax, group_tax_account_template):
        """Account templates (account, refund account) the tax group gives the tax."""
        if tax.deductible:
            account = group_tax_account_template.ded_account_id
            refund_account = group_tax_account_template.ded_refund_account_id
        elif tax.withholdable:
            if tax.type_tax_use == "purchase":
                account = group_tax_account_template.account_id
                refund_account = group_tax_account_template.refund_account_id
            else:
                account = False
                refund_account = False
        elif tax.type_tax_use == "purchase" and tax.tax_group_id == self.env.ref(
            "l10n_br_coa.tax_group_icmsst"
        ):
            # The ICMS ST of a purchase is charged by the supplier
            # and is part of the cost: it has no account. The ST
            # group carries the accounts of the sale side only.
            account = False
            refund_account = False
        else:
            account = group_tax_account_template[
                ACC_NAMES.get(tax.type_tax_use, {}).get("account_id")
            ]
            refund_account = group_tax_account_template[
                ACC_NAMES.get(tax.type_tax_use, {}).get("refund_account_id")
            ]
        return account, refund_account
