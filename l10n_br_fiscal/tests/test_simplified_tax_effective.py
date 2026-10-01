# Copyright 2026 Engenere - Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, new_test_user

from ..constants.fiscal import TAX_FRAMEWORK_NORMAL, TAX_FRAMEWORK_SIMPLES


class TestSimplifiedTaxEffective(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.annexes = cls.env["l10n_br_fiscal.simplified.tax"].search([])
        cls.company_sn = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.company_normal = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.cfop_industry = cls.env.ref("l10n_br_fiscal.cfop_5101")
        cls.cfop_commerce = cls.env.ref("l10n_br_fiscal.cfop_5102")
        # may change the company but is not a fiscal manager
        cls.user_admin = new_test_user(
            cls.env,
            login="sn_company_admin",
            groups="base.group_system,base.group_partner_manager,"
            "l10n_br_fiscal.group_user",
            company_id=cls.company_sn.id,
            company_ids=[(6, 0, (cls.company_sn + cls.company_normal).ids)],
        )

    def _get_icms_credit_percent(self, cfop):
        tax_range = self.company_sn._get_simplified_tax_range(cfop)
        return tax_range._get_effective_tax_percent(
            self.company_sn.annual_revenue, "icms"
        )

    def test_lines_follow_company_tax_framework(self):
        self.assertFalse(self.company_normal.sn_effective_tax_ids)
        self.company_normal.tax_framework = TAX_FRAMEWORK_SIMPLES
        self.assertEqual(
            self.company_normal.sn_effective_tax_ids.simplified_tax_id, self.annexes
        )
        self.company_normal.tax_framework = TAX_FRAMEWORK_NORMAL
        self.assertFalse(self.company_normal.sn_effective_tax_ids)

    def test_lines_follow_partner_tax_framework(self):
        partner = self.company_normal.partner_id
        partner.tax_framework = TAX_FRAMEWORK_SIMPLES
        self.assertEqual(self.company_normal.tax_framework, TAX_FRAMEWORK_SIMPLES)
        self.assertEqual(
            self.company_normal.sn_effective_tax_ids.simplified_tax_id, self.annexes
        )
        partner.tax_framework = TAX_FRAMEWORK_NORMAL
        self.assertFalse(self.company_normal.sn_effective_tax_ids)

    def test_lines_of_companies_created_in_batch(self):
        companies = self.env["res.company"].create(
            [
                {"name": "SN batch 1", "tax_framework": TAX_FRAMEWORK_SIMPLES},
                {"name": "SN batch 2", "tax_framework": TAX_FRAMEWORK_SIMPLES},
                {"name": "Normal batch", "tax_framework": TAX_FRAMEWORK_NORMAL},
            ]
        )
        for company in companies[:2]:
            self.assertEqual(
                company.sn_effective_tax_ids.simplified_tax_id, self.annexes
            )
        self.assertFalse(companies[2].sn_effective_tax_ids)

    def test_lines_restored_on_company_without_them(self):
        """What the migration does for the companies that were already under
        the Simples Nacional before the effective tax lines existed."""
        self.company_sn.sn_effective_tax_ids.unlink()
        self.company_sn._update_effective_tax_lines()
        self.assertEqual(
            self.company_sn.sn_effective_tax_ids.simplified_tax_id, self.annexes
        )
        self.assertAlmostEqual(
            max(self.company_sn.sn_effective_tax_ids.mapped("tax_icms_percent")),
            2.70,
            2,
        )

    def test_lines_removed_by_non_fiscal_manager(self):
        company = self.company_sn.with_user(self.user_admin)
        company.tax_framework = TAX_FRAMEWORK_NORMAL
        self.assertFalse(self.company_sn.sn_effective_tax_ids)

    def test_icmssn_credit_follows_annual_revenue(self):
        self.assertAlmostEqual(
            self._get_icms_credit_percent(self.cfop_industry), 2.70, 2
        )
        self.assertAlmostEqual(
            self._get_icms_credit_percent(self.cfop_commerce), 2.66, 2
        )
        # Faixa 1: 4,5% x 32% no Anexo 2 e 4% x 34% no Anexo 1
        self.company_sn.annual_revenue = 100000.0
        self.assertAlmostEqual(
            self._get_icms_credit_percent(self.cfop_industry), 1.44, 2
        )
        self.assertAlmostEqual(
            self._get_icms_credit_percent(self.cfop_commerce), 1.36, 2
        )

    def test_icmssn_credit_of_renamed_annex(self):
        self.env.ref("l10n_br_fiscal.simplefied_tax_anexo1").name = "Anexo I"
        self.env.ref("l10n_br_fiscal.simplefied_tax_anexo2").name = "Anexo II"
        self.company_sn.invalidate_recordset()
        self.assertAlmostEqual(
            self._get_icms_credit_percent(self.cfop_industry), 2.70, 2
        )
        self.assertAlmostEqual(
            self._get_icms_credit_percent(self.cfop_commerce), 2.66, 2
        )

    def test_effective_tax_above_the_last_range(self):
        lines = self.company_sn.sn_effective_tax_ids
        self.assertTrue(all(lines.mapped("current_effective_tax")))
        self.company_sn.annual_revenue = 5000000.0
        self.assertFalse(lines.current_range_id)
        self.assertEqual(lines.mapped("current_effective_tax"), [0.0] * len(lines))

    def test_range_effective_tax(self):
        annex = self.env.ref("l10n_br_fiscal.simplefied_tax_anexo2")
        # Faixa 4: (815.000 x 11,2% - 22.500) / 815.000 = 8,44%, sendo 32% de ICMS
        tax_range = annex._get_range(815000.0)
        self.assertEqual(tax_range.name, "Faixa 4")
        self.assertAlmostEqual(tax_range._get_effective_tax(815000.0), 8.44, 2)
        self.assertAlmostEqual(
            tax_range._get_effective_tax_percent(815000.0, "icms"), 2.70, 2
        )
        self.assertAlmostEqual(
            tax_range._get_effective_tax_percent(815000.0, "ipi"), 0.63, 2
        )

    def test_range_effective_tax_without_revenue(self):
        """First month of activity: the lowest rate of the annex
        (LC 123/2006, art. 23, § 3º)."""
        annex = self.env.ref("l10n_br_fiscal.simplefied_tax_anexo2")
        tax_range = annex._get_range(0.0)
        self.assertEqual(tax_range.name, "Faixa 1")
        self.assertAlmostEqual(tax_range._get_effective_tax(0.0), 4.50, 2)
        self.assertAlmostEqual(
            tax_range._get_effective_tax_percent(0.0, "icms"), 1.44, 2
        )

    def test_range_effective_tax_above_the_last_range(self):
        annex = self.env.ref("l10n_br_fiscal.simplefied_tax_anexo2")
        tax_range = annex._get_range(5000000.0)
        self.assertFalse(tax_range)
        self.assertEqual(tax_range._get_effective_tax(5000000.0), 0.0)
        self.assertEqual(tax_range._get_effective_tax_percent(5000000.0, "icms"), 0.0)

    def test_no_range_for_company_outside_the_simples(self):
        self.company_normal.annual_revenue = 815000.0
        tax_range = self.company_normal._get_simplified_tax_range(self.cfop_industry)
        self.assertFalse(tax_range)
