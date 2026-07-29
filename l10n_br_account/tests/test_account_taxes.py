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
        l10n_br_coa_charts = (
            self.env["account.chart.template"]
            .search([])
            .filtered(
                lambda chart: chart.get_external_id()
                .get(chart.id)
                .split(".")[0]
                .startswith("l10n_br_coa_")
                if chart.get_external_id().get(chart.id)
                else False
            )
        )
        for l10n_br_coa_chart in l10n_br_coa_charts:
            l10n_br_coa_chart.try_loading()
            account_taxes = self.env["account.tax"].search(
                [("company_id", "=", self.l10n_br_company.id)]
            )

            is_fiscal_taxes = False
            for tax in account_taxes:
                if tax.tax_group_id.fiscal_tax_group_id and tax.fiscal_tax_ids:
                    is_fiscal_taxes = True

            assert is_fiscal_taxes, "There are not fiscal taxes related"

    def test_load_fiscal_taxes_manual_tax(self):
        """Taxes created by hand have no XML ID and must be skipped"""
        coa_template = self.env["account.chart.template"].create(
            {
                "name": "Plano de Contas Teste",
                "parent_id": self.env.ref("l10n_br_coa.l10n_br_coa_template").id,
                "currency_id": self.env.ref("base.BRL").id,
                "bank_account_code_prefix": "1.1.1.2",
                "cash_account_code_prefix": "1.1.1.1",
                "transfer_account_code_prefix": "1.1.1.3",
            }
        )
        self.l10n_br_company.chart_template_id = coa_template
        manual_tax = self.env["account.tax"].create(
            {
                "name": "IRRF Manual",
                "amount": 1.5,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "company_id": self.l10n_br_company.id,
            }
        )

        self.assertFalse(manual_tax.get_external_id().get(manual_tax.id))

        coa_template.load_fiscal_taxes()

        self.assertFalse(manual_tax.fiscal_tax_ids)
