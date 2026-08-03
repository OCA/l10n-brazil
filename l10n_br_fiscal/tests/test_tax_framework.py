# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase

from ..constants.fiscal import TAX_FRAMEWORK_SIMPLES_ALL


class TestTaxFramework(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.company

    def test_mei_is_simples_nacional_all(self):
        self.assertIn("4", TAX_FRAMEWORK_SIMPLES_ALL)

    def test_mei_gets_simples_nacional_taxes_onchange(self):
        self.company.tax_framework = "4"
        self.company._onchange_profit_calculation()
        self.assertEqual(
            self.company.tax_icms_id,
            self.env.ref("l10n_br_fiscal.tax_icms_sn_com_credito"),
        )
        self.assertEqual(
            self.company.piscofins_id,
            self.env.ref("l10n_br_fiscal.tax_pis_cofins_simples_nacional"),
        )
