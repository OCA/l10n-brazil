# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("br_oca", "account.tax")
    def _get_br_oca_fiscal_account_tax(self):
        return self._link_existing_fiscal_tax_groups_to_account_tax_data(
            self._parse_csv("br_oca", "account.tax", module="l10n_br_account")
        )

    @template("br_oca", "account.tax.group")
    def _get_br_oca_fiscal_account_tax_group(self):
        return self._parse_csv("br_oca", "account.tax.group", module="l10n_br_account")

    def _link_existing_fiscal_tax_groups_to_account_tax_data(self, data):
        group_key = "fiscal_tax_ids@tax_group_id"
        for rec_data in data.values():
            if group_key not in rec_data:
                continue
            rec_data["fiscal_tax_ids"] = [
                Command.set(
                    self.env["l10n_br_fiscal.tax"]
                    .search(
                        [("tax_group_id", "=", self.env.ref(rec_data[group_key]).id)]
                    )
                    .ids
                )
            ]
            del rec_data[group_key]
        return data
