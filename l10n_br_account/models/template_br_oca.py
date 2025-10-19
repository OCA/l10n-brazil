# Copyright 2019-TODAY Akretion - Renato Lima
# Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def load_fiscal_taxes(self, companies=None):
        """
        Create missing account.tax for Brazil.
        Add missing account.account for the Brazilian taxes.
        Relate account taxes with fiscal taxes to enable the Brazilian
        tax engine to kick in with the installed chart of account.
        """
        tax_group_data = self._parse_csv(
            "br_oca", "account.tax.group", module="l10n_br_coa"
        )
        tax_group_data_rel = self._parse_csv(
            "br_oca", "account.tax.group", module="l10n_br_account"
        )
        tax_data = self._parse_csv("br_oca", "account.tax", module="l10n_br_coa")

        if companies is None:
            companies = self.env["res.company"].search(
                [("chart_template", "=", "br_oca")]
            )

        for company in companies:
            for key, value in tax_group_data.items():
                id_key = f"{company.id}_{key}"
                existing_group = self.env.ref(
                    f"l10n_br_coa.{id_key}", raise_if_not_found=False
                )
                if existing_group:
                    continue
                else:
                    group_vals = {
                        "name": value["name"],
                        "company_id": company.id,
                    }
                    if key in tax_group_data_rel:
                        group_vals["fiscal_tax_group_id"] = self.env.ref(
                            tax_group_data_rel[key]["fiscal_tax_group_id"]
                        ).id

                    tax_group = self.env["account.tax.group"].create(group_vals)
                    self.env["ir.model.data"].create(
                        {
                            "name": id_key,
                            "module": "l10n_br_coa",
                            "model": "account.tax.group",
                            "res_id": tax_group.id,
                            "noupdate": True,
                        }
                    )
            for key, value in tax_data.items():
                id_key = f"{company.id}_{key}"
                existing_tax = self.env.ref(
                    f"l10n_br_coa.{id_key}", raise_if_not_found=False
                )
                if existing_tax:  # TODO also check record/res_id
                    continue
                else:
                    tax_vals = {
                        "name": value["name"],
                        "company_id": company.id,
                        "tax_group_id": self.env.ref(
                            f"l10n_br_coa.{company.id}_{value['tax_group_id']}"
                        ).id,
                        "type_tax_use": value["type_tax_use"],
                        "price_include": value["price_include"],
                        "deductible": value["deductible"],
                        "withholdable": value["withholdable"],
                    }

                    account_tax = self.env["account.tax"].create(tax_vals)
                    self.env["ir.model.data"].create(
                        {
                            "name": id_key,
                            "module": "l10n_br_coa",
                            "model": "account.tax",
                            "res_id": account_tax.id,
                            "noupdate": True,
                        }
                    )

            self.env["account.chart.template"]._populate_default_br_tax_accounts(
                company, flavor="cfc", review_suffix=""
            )
