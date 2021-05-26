# Copyright (C) 2020  Renato Lima - Akretion
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import TransactionCase


class L10nBrCoaComplete(TransactionCase):
    def setUp(self):
        super().setUp()

        self.l10n_br_coa_complete = self.env.ref(
            'l10n_br_coa_complete.l10n_br_coa_complete_template')
        self.l10n_br_company = self.env['res.company'].create({
            'name': 'Empresa Teste do Plano de Contas CFC'
        })

    def test_l10n_br_coa_complete(self):
        """Test to install the chart of accounts template in a new company"""
        self.env.user.company_ids += self.l10n_br_company
        self.env.user.company_id = self.l10n_br_company
        self.l10n_br_coa_complete.try_loading_for_current_company()

        self.assertEqual(
            self.l10n_br_coa_complete, self.l10n_br_company.chart_template_id)
