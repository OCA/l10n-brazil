# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class L10nBrCoaGeneric(TransactionCase):
    def setUp(self):
        super().setUp()

        self.l10n_br_coa_generic = self.env.ref(
            "l10n_br_coa_generic.l10n_br_coa_generic_template"
        )
        self.l10n_br_company = self.env["res.company"].create(
            {"name": "Empresa Teste do Plano de Contas CFC"}
        )

    def test_l10n_br_coa_generic(self):
        """Test installing the chart of accounts template in a new company"""
        self.l10n_br_coa_generic.try_loading(company=self.l10n_br_company)
        self.assertEqual(
            self.l10n_br_coa_generic, self.l10n_br_company.chart_template_id
        )
