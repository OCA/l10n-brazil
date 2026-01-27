# Copyright (C) KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("br_oca_generic")
    def _get_br_oca_generic_template_data(self):
        return {
            "name": _("Plano de Contas para empresas do Regime normal"),
            "parent": "br_oca",
            "visible": True,
            "property_account_receivable_id": "coa_generic_112101",
            "property_account_payable_id": "coa_generic_211101",
            "property_account_expense_categ_id": "coa_generic_511101",
            "property_account_income_categ_id": "coa_generic_611101",
        }

    @template("br_oca_generic", "res.company")
    def _get_br_oca_generic_res_company(self):
        return {
            self.env.company.id: {
                "account_default_pos_receivable_account_id": "coa_generic_112102",
                "anglo_saxon_accounting": True,
            },
        }
