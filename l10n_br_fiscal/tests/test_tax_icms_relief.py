# Copyright 2026 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import TransactionCase


class TestTaxIcmsRelief(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nfe_tax_benefit = cls.env.ref("l10n_br_fiscal.demo_nfe_tax_benefit")
        cls.icms_relief = cls.env.ref("l10n_br_fiscal.icms_relief_9")
        cls.tax_benefit = cls.env["l10n_br_fiscal.tax.definition"].create(
            {
                "icms_regulation_id": cls.env.ref(
                    "l10n_br_fiscal.tax_icms_regulation"
                ).id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_icms").id,
                "code": "SP810002",
                "name": "TAX BENEFIT DEMO RELIEF",
                "description": "TAX BENEFIT DEMO RELIEF",
                "benefit_type": "1",
                "is_benefit": True,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "icms_relief_id": cls.icms_relief.id,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_icms_12_red_26_57").id,
                "cst_id": cls.env.ref("l10n_br_fiscal.cst_icms_20").id,
                "state_from_id": cls.env.ref("base.state_br_sp").id,
                "state_to_ids": [Command.set(cls.env.ref("base.state_br_mg").ids)],
                "ncms": "73269090",
                "ncm_ids": [
                    Command.set(cls.env.ref("l10n_br_fiscal.ncm_73269090").ids)
                ],
                "state": "approved",
            }
        )
        # force update
        cls.nfe_tax_benefit.fiscal_line_ids._compute_fiscal_tax_ids()

    def test_nfe_tax_icms_relief(self):
        """Test NFe document line gets icms_relief_id from the tax benefit."""
        for line in self.nfe_tax_benefit.fiscal_line_ids:
            self.assertEqual(
                line.icms_tax_benefit_id,
                self.tax_benefit,
                "Document line must have tax benefit",
            )
            self.assertEqual(
                line.icms_relief_id,
                self.icms_relief,
                "Document line must have ICMS relief",
            )
