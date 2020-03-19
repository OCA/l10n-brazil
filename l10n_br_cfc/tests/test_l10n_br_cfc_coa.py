# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class L10nBrCfcCOA(TransactionCase):
    def setUp(self):
        super(L10nBrCfcCOA, self).setUp()

        self.l10n_br_cfc_coa = self.env.ref(
            'l10n_br_cfc.l10n_br_cfc_chart_template')
        self.l10n_br_company = self.env['res.company'].create({
            'name': 'Empresa Teste do Plano de Contas CFC'
        })

    def test_l10n_br_cfc_coa(self):
        """Test to install the chart of accounts template in a new company"""
        self.env.user.company_ids += self.l10n_br_company
        self.env.user.company_id = self.l10n_br_company
        self.l10n_br_cfc_coa.try_loading_for_current_company()

        self.assertEquals(
            self.l10n_br_cfc_coa, self.l10n_br_company.chart_template_id)
