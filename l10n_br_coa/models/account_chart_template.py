# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

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

            acc_names = {
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

            for tax in taxes_ref.values():
                domain = [
                    ("tax_group_id", "=", tax.tax_group_id.id),
                    ("chart_template_id", "=", self.id),
                ]
                group_tax_account_template = self.env[
                    "l10n_br_coa.account.tax.group.account.template"
                ].search(domain)
                if group_tax_account_template:
                    if tax.deductible:
                        account = group_tax_account_template.ded_account_id
                        refund_account = (
                            group_tax_account_template.ded_refund_account_id
                        )
                    elif tax.withholdable:
                        if tax.type_tax_use == "purchase":
                            account = group_tax_account_template.account_id
                            refund_account = (
                                group_tax_account_template.refund_account_id
                            )
                        else:
                            account = False
                            refund_account = False
                    else:
                        account = group_tax_account_template[
                            acc_names.get(tax.type_tax_use, {}).get("account_id")
                        ]
                        refund_account = group_tax_account_template[
                            acc_names.get(tax.type_tax_use, {}).get("refund_account_id")
                        ]

                    account_id = account_ref[account.id].id if account else False
                    refund_account_id = (
                        account_ref[refund_account.id].id if refund_account else False
                    )
                    tax._update_repartition_lines(account_id, refund_account_id)

        return account_ref, taxes_ref
