# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def load_for_current_company(self, sale_tax_rate, purchase_tax_rate):
        self.ensure_one()
        super().load_for_current_company(sale_tax_rate, purchase_tax_rate)
        # Remove Company default taxes configuration
        if self.currency_id == self.env.ref("base.BRL"):
            self.env.company.write(
                {
                    "account_sale_tax_id": False,
                    "account_purchase_tax_id": False,
                }
            )

    def _load_template(
        self, company, code_digits=None, account_ref=None, taxes_ref=None
    ):
        self.ensure_one()
        account_ref, taxes_ref = super()._load_template(
            company, code_digits, account_ref, taxes_ref
        )

        if self.parent_id:

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

            taxes = self.env["account.tax"].browse(taxes_ref.values())
            for tax in taxes:
                domain = [
                    ("tax_group_id", "=", tax.tax_group_id.id),
                    ("chart_template_id", "=", self.id),
                ]
                group_tax_account_template = self.env[
                    "l10n_br_coa.account.tax.group.account.template"
                ].search(domain)
                if group_tax_account_template:
                    if tax.deductible:
                        account_id = group_tax_account_template.ded_account_id
                        refund_account_id = (
                            group_tax_account_template.ded_refund_account_id
                        )
                    else:
                        account_id = group_tax_account_template[
                            acc_names.get(tax.type_tax_use, {}).get("account_id")
                        ]
                        refund_account_id = group_tax_account_template[
                            acc_names.get(tax.type_tax_use, {}).get("refund_account_id")
                        ]

                    tax.write(
                        {
                            "invoice_repartition_line_ids": [
                                (5, 0, 0),
                                (
                                    0,
                                    0,
                                    {
                                        "factor_percent": 100,
                                        "repartition_type": "base",
                                    },
                                ),
                                (
                                    0,
                                    0,
                                    {
                                        "factor_percent": 100
                                        if not tax.deductible
                                        else -100,
                                        "repartition_type": "tax",
                                        "account_id": account_ref.get(
                                            account_id.id, False
                                        ),
                                    },
                                ),
                            ],
                            "refund_repartition_line_ids": [
                                (5, 0, 0),
                                (
                                    0,
                                    0,
                                    {
                                        "factor_percent": 100,
                                        "repartition_type": "base",
                                    },
                                ),
                                (
                                    0,
                                    0,
                                    {
                                        "factor_percent": 100
                                        if not tax.deductible
                                        else -100,
                                        "repartition_type": "tax",
                                        "account_id": account_ref.get(
                                            refund_account_id.id, False
                                        ),
                                    },
                                ),
                            ],
                        }
                    )
        return account_ref, taxes_ref
