# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class L10nBrCoaGeneric(TransactionCase):
    def setUp(self):
        super().setUp()

        self.l10n_br_company = self.env["res.company"].create(
            {"name": "Empresa Teste do Plano de Contas CFC"}
        )

    def test_chart_template_is_defined(self):
        templates = self.env["account.chart.template"]._get_chart_template_mapping()
        self.assertTrue(
            "br_oca_generic" in templates,
            "Chart template br_oca_generic is not defined",
        )

    def test_l10n_br_coa_generic(self):
        """Test installing the chart of accounts template in a new company"""
        self.env["account.chart.template"].try_loading(
            "br_oca_generic", self.l10n_br_company
        )
        self.assertEqual("br_oca_generic", self.l10n_br_company.chart_template)
