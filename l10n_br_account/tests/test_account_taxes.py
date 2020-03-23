# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class TestAccountTaxes(TransactionCase):
    def setUp(self):
        super(TestAccountTaxes, self).setUp()

        self.l10n_br_simple_coa = self.env.ref(
            'l10n_br_simple.l10n_br_simple_chart_template')
        self.l10n_br_company = self.env['res.company'].create({
            'name': 'Empresa Teste do Plano de Contas Simplificado'})

    def test_load_coa(self):
        """Test to install the chart of accounts template in a new company"""
        self.env.user.company_ids += self.l10n_br_company
        self.env.user.company_id = self.l10n_br_company
        self.l10n_br_simple_coa.try_loading_for_current_company()

        self.assertEquals(
            self.l10n_br_simple_coa, self.l10n_br_company.chart_template_id)

    def test_account_taxes(self):
        """Test if account taxes are related with fiscal taxes"""
        account_taxes = self.env['account.tax'].search(
            [('company_id', '=', self.l10n_br_company.id)])

        is_fiscal_taxes = False
        for tax in account_taxes:
            if tax.tax_group_id.fiscal_group_id and tax.fiscal_tax_ids:
                is_fiscal_taxes = True

        assert(is_fiscal_taxes,
               "There are not fiscal taxes related with account taxes")
