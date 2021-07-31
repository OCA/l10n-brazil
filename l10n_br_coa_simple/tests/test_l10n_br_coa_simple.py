# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class L10nBrSimpleCOA(TransactionCase):
    def setUp(self):
        super(L10nBrSimpleCOA, self).setUp()

        self.l10n_br_coa_simple = self.env.ref(
            "l10n_br_coa_simple.l10n_br_coa_simple_chart_template"
        )
        self.l10n_br_company = self.env["res.company"].create(
            {"name": "Empresa Teste do Plano de Contas Simplificado"}
        )

    def test_l10n_br_coa_simple(self):
        """Test to install the chart of accounts template in a new company"""
        self.env.user.company_ids += self.l10n_br_company
        self.env.user.company_id = self.l10n_br_company
        self.l10n_br_coa_simple.try_loading_for_current_company()

        self.assertEqual(
            self.l10n_br_coa_simple, self.l10n_br_company.chart_template_id
        )
