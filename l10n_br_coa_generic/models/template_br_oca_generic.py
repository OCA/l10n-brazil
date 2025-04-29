# Copyright 2025 Escodoo - Marcel Savegnago <https://www.escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("br_oca_generic")
    def _get_br_oca_generic_template_data(self):
        return {
            "name": _("Plano de Contas Genérico para Empresas do Regime normal"),
            "parent": "br_oca",
            "use_anglo_saxon": True,
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
            },
        }

    @template("br_oca", "account.tax")
    def _get_br_oca_force_account_tax(self):
        tax_data = self._parse_csv("br_oca", "account.tax", module="l10n_br_coa")
        self._set_tax_group_accs("br_oca_generic", tax_data)
        return tax_data

    @template("br_oca", "account.tax.group")
    def _get_br_oca_force_account_tax_group(self):
        return self._parse_csv("br_oca", "account.tax.group", module="l10n_br_coa")

    def _get_tax_group_accounts(self, template_code):
        """
        Default invoice/refund accounts by tax group
        Data previously populated
        l10n_br_coa.account.tax.group.account.template
        in <v17, when CoA template models was used

        [tax_group_id xmlid (pseudo)]: {
            ded_account_id: xmlid
            ded_refund_account_id: xmlid
            account_id: xmlid
            refund_account_id: xmlid
        }
        """
        if template_code != "br_oca_generic":
            return super()._get_tax_group_accounts(template_code)

        return {
            "tax_group_icms": {
                "account_id": "coa_generic_217103",
                "refund_account_id": "coa_generic_114102",
                "ded_account_id": "coa_generic_611203",
                "ded_refund_account_id": "coa_generic_611223",
            },
            "tax_group_ipi": {
                "account_id": "coa_generic_217102",
                "refund_account_id": "coa_generic_114101",
                "ded_account_id": "coa_generic_611208",
                "ded_refund_account_id": "coa_generic_611228",
            },
            "tax_group_pis": {
                "account_id": "coa_generic_217105",
                "refund_account_id": "coa_generic_114105",
                "ded_account_id": "coa_generic_611206",
                "ded_refund_account_id": "coa_generic_611226",
            },
            "tax_group_cofins": {
                "account_id": "coa_generic_217104",
                "refund_account_id": "coa_generic_114104",
                "ded_account_id": "coa_generic_611205",
                "ded_refund_account_id": "coa_generic_611225",
            },
            "tax_group_issqn": {
                "account_id": "coa_generic_217108",
                "refund_account_id": "coa_generic_114109",
                "ded_account_id": "coa_generic_611204",
                "ded_refund_account_id": "coa_generic_611224",
            },
            "tax_group_csll": {
                "account_id": "coa_generic_217107",
                "refund_account_id": "coa_generic_114107",
                "ded_account_id": "coa_generic_611209",
                "ded_refund_account_id": "coa_generic_611229",
            },
            "tax_group_irpj": {
                "account_id": "coa_generic_217106",
                "refund_account_id": "coa_generic_114106",
                "ded_account_id": "coa_generic_611210",
                "ded_refund_account_id": "coa_generic_611230",
            },
            "tax_group_ii": {
                "account_id": "coa_generic_217113",
                "refund_account_id": "coa_generic_114110",
                "ded_account_id": "coa_generic_611211",
                "ded_refund_account_id": "coa_generic_611231",
            },
            "tax_group_pis_wh": {
                "account_id": "coa_generic_217105",
                "refund_account_id": "coa_generic_114105",
                "ded_account_id": False,
                "ded_refund_account_id": False,
            },
            "tax_group_cofins_wh": {
                "account_id": "coa_generic_217104",
                "refund_account_id": "coa_generic_114104",
                "ded_account_id": False,
                "ded_refund_account_id": False,
            },
            "tax_group_issqn_wh": {
                "account_id": "coa_generic_217108",
                "refund_account_id": "coa_generic_114109",
                "ded_account_id": False,
                "ded_refund_account_id": False,
            },
            "tax_group_csll_wh": {
                "account_id": "coa_generic_217107",
                "refund_account_id": "coa_generic_114107",
                "ded_account_id": False,
                "ded_refund_account_id": False,
            },
            "tax_group_irpj_wh": {
                "account_id": "coa_generic_217106",
                "refund_account_id": "coa_generic_114106",
                "ded_account_id": False,
                "ded_refund_account_id": False,
            },
            "tax_group_inss_wh": {
                "account_id": "coa_generic_216101",
                "refund_account_id": "coa_generic_114111",
                "ded_account_id": False,
                "ded_refund_account_id": False,
            },
        }
