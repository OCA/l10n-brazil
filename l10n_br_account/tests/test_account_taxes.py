# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import TransactionCase


class TestAccountTaxes(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.l10n_br_company = cls.env["res.company"].create(
            {"name": "Empresa Teste do Plano de Contas Simplificado"}
        )
        cls.env.user.company_ids += cls.l10n_br_company
        cls.env.company = cls.l10n_br_company

    def test_account_taxes(self):
        """Test if account taxes are related with fiscal taxes"""
        template = self.env["account.chart.template"]
        for chart, chart_data in template._get_chart_template_mapping().items():
            if "br_oca" not in template._get_parent_template(chart):
                continue
            if (
                self.env["ir.module.module"]._get(chart_data["module"]).state
                != "installed"
            ):
                continue
            template.try_loading(chart, self.l10n_br_company)
            account_taxes = self.env["account.tax"].search(
                [("company_id", "=", self.l10n_br_company.id)]
            )

            is_fiscal_taxes = False
            for tax in account_taxes:
                if tax.tax_group_id.fiscal_tax_group_id and tax.fiscal_tax_ids:
                    is_fiscal_taxes = True

            assert is_fiscal_taxes, "There are not fiscal taxes related"
