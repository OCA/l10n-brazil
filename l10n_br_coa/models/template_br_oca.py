# Copyright 2020 KMEE
# Copyright 2025 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, _, models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("br_oca")
    def _get_br_oca_template_data(self):
        return {
            "name": _("Plano de Contas Base"),
            "visible": False,
            "code_digits": "2",
            "use_anglo_saxon": False,
        }

    @template("br_oca", "res.company")
    def _get_br_oca_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.br",
                "cash_account_code_prefix": "1.1.1.1.",
                "bank_account_code_prefix": "1.1.1.2.",
                "transfer_account_code_prefix": "1.1.1.2.0",
                "account_sale_tax_id": False,
                "account_purchase_tax_id": False,
            },
        }

    def _set_tax_group_accs(self, template_code, tax_data):
        group_to_accounts = self._get_tax_group_accounts(template_code)
        for tax in tax_data.values():
            if (
                tax.get("tax_group_id") not in group_to_accounts
                or tax.get("type_tax_use") not in ("sale", "purchase", "all")
                or tax.get("repartition_line_ids")
            ):
                continue
            accs = group_to_accounts[tax["tax_group_id"]]
            if tax.get("deductible"):
                account_id = accs.get("ded_account_id", False)
                refund_account_id = accs.get("ded_refund_account_id", False)
            elif tax.get("withholdable") and tax["type_tax_use"] != "purchase":
                account_id = False
                refund_account_id = False
            else:
                account_id = accs.get("account_id", False)
                refund_account_id = accs.get("refund_account_id", False)
                if not tax.get("withholdable") and tax["type_tax_use"] == "purchase":
                    account_id, refund_account_id = refund_account_id, account_id

            for fname in (
                "invoice_repartition_line_ids",
                "refund_repartition_line_ids",
            ):
                if not tax.get(fname):
                    tax[fname] = [
                        Command.create({"repartition_type": "base"}),
                        Command.create({"repartition_type": "tax"}),
                    ]
                is_refund = fname == "refund_repartition_line_ids"
                for _command, _id, repartition in tax[fname]:
                    repartition["account_id"] = (
                        refund_account_id if is_refund else account_id
                    )
                    repartition["factor_percent"] = (
                        -1 if tax.get("deductible") or tax.get("withholdable") else 1
                    ) * 100

    def _get_tax_group_accounts(self, template_code):
        """
        Default invoice/refund accounts by tax group
        Data previously populated l10n_br_coa.account.tax.group.account.template
        until v16, when CoA template models was used

        [tax_group_id xmlid (pseudo)]: {
            ded_account_id: xmlid
            ded_refund_account_id: xmlid
            account_id: xmlid
            refund_account_id: xmlid
        }
        """
        return dict()
