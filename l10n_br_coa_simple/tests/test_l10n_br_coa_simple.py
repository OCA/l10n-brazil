# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class L10nBrSimpleCOA(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.l10n_br_coa_simple = cls.env.ref(
            "l10n_br_coa_simple.l10n_br_coa_simple_chart_template"
        )
        cls.l10n_br_company = cls.env["res.company"].create(
            {"name": "Empresa Teste do Plano de Contas Simplificado"}
        )

    def test_l10n_br_coa_simple(self):
        """Test installing the chart of accounts template in a new company"""
        self.l10n_br_coa_simple.try_loading(company=self.l10n_br_company)
        self.assertEqual(
            self.l10n_br_coa_simple, self.l10n_br_company.chart_template_id
        )
