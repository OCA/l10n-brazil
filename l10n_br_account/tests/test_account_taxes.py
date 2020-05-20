# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class TestAccountTaxes(TransactionCase):
    def setUp(self):
        super(TestAccountTaxes, self).setUp()

        self.l10n_br_company = self.env['res.company'].create({
            'name': 'Empresa Teste do Plano de Contas Simplificado'})

        self.env.user.company_ids += self.l10n_br_company
        self.env.user.company_id = self.l10n_br_company

    def test_account_taxes(self):
        """Test if account taxes are related with fiscal taxes"""
        l10n_br_coa_charts = self.env["account.chart.template"].search(
            []).filtered(
                lambda chart: chart.get_external_id().get(
                    chart.id).split('.')[0].startswith("l10n_br_coa_")
                if chart.get_external_id().get(chart.id) else False
        )
        for l10n_br_coa_chart in l10n_br_coa_charts:
            l10n_br_coa_chart.try_loading_for_current_company()
            account_taxes = self.env['account.tax'].search(
                [('company_id', '=', self.l10n_br_company.id)])

            is_fiscal_taxes = False
            for tax in account_taxes:
                if tax.tax_group_id.fiscal_tax_group_id and \
                        tax.fiscal_tax_ids:
                    is_fiscal_taxes = True

            assert is_fiscal_taxes, "There are not fiscal taxes related"
