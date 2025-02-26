# Copyright 2023 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError
from odoo.tests import SavepointCase


class TestTaxBenefit(SavepointCase):
    def setUp(self):
        super().setUp()
        self.nfe_tax_benefit = self.env.ref("l10n_br_fiscal.demo_nfe_tax_benefit")
        self.icms_benefit = self.env["l10n_br_fiscal.icms.benefit"].create(
            {
                "code": "SP810001",
                "description": "TAX BENEFIT DEMO",
            }
        )
        self.tax_benefit = self.env["l10n_br_fiscal.tax.definition"].create(
            {
                "icms_regulation_id": self.env.ref(
                    "l10n_br_fiscal.tax_icms_regulation"
                ).id,
                "tax_group_id": self.env.ref("l10n_br_fiscal.tax_group_icms").id,
                "name": "TAX BENEFIT DEMO",
                "is_benefit": True,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": self.env.ref("l10n_br_fiscal.tax_icms_12_red_26_57").id,
                "cst_id": self.env.ref("l10n_br_fiscal.cst_icms_20").id,
                "state_to_ids": [(6, 0, self.env.ref("base.state_br_mg").ids)],
                "ncms": "73269090",
                "ncm_ids": [(6, 0, self.env.ref("l10n_br_fiscal.ncm_73269090").ids)],
                "state": "approved",
                "icms_tax_benefit_id": self.icms_benefit.id,
            }
        )

    def test_nfe_tax_benefit(self):
        """Test NFe with tax benefit."""

        self.nfe_tax_benefit._onchange_document_serie_id()
        self.nfe_tax_benefit._onchange_fiscal_operation_id()
        self.tax_benefit.fiscal_operation_line_id = (
            self.nfe_tax_benefit.fiscal_operation_id.line_ids[:1]
        )

        for line in self.nfe_tax_benefit.fiscal_line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

            self.assertEqual(
                line.icms_tax_benefit_id,
                self.tax_benefit.icms_tax_benefit_id,
                "Document line must have tax benefit",
            )
            self.assertEqual(
                self.tax_benefit.display_name,
                "ICMS-ICMS 12% Com Red. 26,57%-20-SP810001",
            )
            self.assertEqual(self.icms_benefit.type, "1")
            self.assertEqual(self.icms_benefit.display_name, "SP810001")
            self.assertEqual(self.icms_benefit.state_id.code, "SP")
            self.assertEqual(
                self.icms_benefit.name_get(), [(self.icms_benefit.id, "SP810001")]
            )
            self.icms_benefit.code = "SP090081"
            with self.assertRaises(UserError):
                self.icms_benefit._compute_type()

    def test_invalid_tax_benefit_code(self):
        with self.assertRaises(ValidationError):
            self.icms_benefit = self.env["l10n_br_fiscal.icms.benefit"].create(
                {
                    "code": "SP81",
                    "description": "Invalid Tax Benefit",
                }
            )
