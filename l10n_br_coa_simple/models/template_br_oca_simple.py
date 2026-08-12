# Copyright (C) KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("br_oca_simple")
    def _get_br_oca_simple_template_data(self):
        return {
            "name": self.env._("Plano de Contas Simplificado"),
            "parent": "br_oca",
            "visible": True,
            "property_account_receivable_id": "coa_simple_1120101",
            "property_account_payable_id": "coa_simple_2120101",
            "property_account_expense_categ_id": "coa_simple_3210101",
            "property_account_income_categ_id": "coa_simple_3110103",
            "income_currency_exchange_account_id": "coa_simple_3410204",
            "expense_currency_exchange_account_id": "coa_simple_3410105",
        }

    @template("br_oca_simple", "res.company")
    def _get_br_oca_simple_res_company(self):
        return {
            self.env.company.id: {
                "account_default_pos_receivable_account_id": "coa_simple_1120101",
                "anglo_saxon_accounting": True,
            },
        }
