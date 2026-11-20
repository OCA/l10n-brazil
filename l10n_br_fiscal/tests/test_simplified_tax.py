# Copyright 2026 Engenere - Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestSimplifiedTax(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_sn = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.company_normal = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.cfop_industry = cls.env.ref("l10n_br_fiscal.cfop_5101")
        cls.cfop_commerce = cls.env.ref("l10n_br_fiscal.cfop_5102")
        cls.annex1 = cls.env.ref("l10n_br_fiscal.simplefied_tax_anexo1")
        cls.annex2 = cls.env.ref("l10n_br_fiscal.simplefied_tax_anexo2")
        cls.annex3 = cls.env.ref("l10n_br_fiscal.simplefied_tax_anexo3")
        cls.annex4 = cls.env.ref("l10n_br_fiscal.simplefied_tax_anexo4")
        cls.annex5 = cls.env.ref("l10n_br_fiscal.simplefied_tax_anexo5")

    def _get_icms_credit_percent(self, cfop):
        tax_range = self.company_sn._get_simplified_tax_range(cfop)
        return tax_range._get_effective_tax_percent(
            self.company_sn.annual_revenue, "icms"
        )

    def _rates_of(self, company, annex):
        return annex.with_context(simplified_tax_company_id=company.id)

    # Effective rates of a range (LC 123/2006, art. 18, § 1º-A and § 1º-B)

    def test_range_effective_tax(self):
        # Faixa 4: (815.000 x 11,2% - 22.500) / 815.000 = 8,44%, sendo 32% de ICMS
        tax_range = self.annex2._get_range(815000.0)
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
        tax_range = self.annex2._get_range(0.0)
        self.assertEqual(tax_range.name, "Faixa 1")
        self.assertAlmostEqual(tax_range._get_effective_tax(0.0), 4.50, 2)
        self.assertAlmostEqual(
            tax_range._get_effective_tax_percent(0.0, "icms"), 1.44, 2
        )

    def test_range_effective_tax_above_the_last_range(self):
        tax_range = self.annex2._get_range(5000000.0)
        self.assertFalse(tax_range)
        self.assertEqual(tax_range._get_effective_tax(5000000.0), 0.0)
        self.assertEqual(tax_range._get_effective_tax_percent(5000000.0, "icms"), 0.0)

    # ICMS credit rate the tax engine uses

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
        self.annex1.name = "Anexo I"
        self.annex2.name = "Anexo II"
        self.assertAlmostEqual(
            self._get_icms_credit_percent(self.cfop_industry), 2.70, 2
        )
        self.assertAlmostEqual(
            self._get_icms_credit_percent(self.cfop_commerce), 2.66, 2
        )

    def test_no_range_without_company(self):
        """A line whose company is not set yet gets no range and no credit."""
        tax_range = self.env["res.company"]._get_simplified_tax_range(
            self.cfop_industry
        )
        self.assertFalse(tax_range)

    def test_no_range_for_company_outside_the_simples(self):
        self.company_normal.annual_revenue = 815000.0
        tax_range = self.company_normal._get_simplified_tax_range(self.cfop_industry)
        self.assertFalse(tax_range)

    # Rates table of the company form

    def test_company_rates_table(self):
        self.assertEqual(
            self.company_sn.simplified_tax_ids,
            self.env["l10n_br_fiscal.simplified.tax"].search([]),
        )
        industry = self._rates_of(self.company_sn, self.annex2)
        self.assertEqual(industry.current_range_id.name, "Faixa 4")
        self.assertAlmostEqual(industry.current_effective_tax, 8.44, 2)
        self.assertAlmostEqual(industry.tax_icms_percent, 2.70, 2)
        commerce = self._rates_of(self.company_sn, self.annex1)
        self.assertAlmostEqual(commerce.current_effective_tax, 7.94, 2)
        self.assertAlmostEqual(commerce.tax_icms_percent, 2.66, 2)

    def test_company_rates_table_of_another_company(self):
        """The same annex shows the rates of the company in the context, not
        the ones of the active company."""
        self.company_normal.annual_revenue = 100000.0
        self.assertEqual(
            self._rates_of(self.company_normal, self.annex2).current_range_id.name,
            "Faixa 1",
        )
        self.assertEqual(
            self._rates_of(self.company_sn, self.annex2).current_range_id.name,
            "Faixa 4",
        )

    def test_company_rates_table_of_unsaved_company(self):
        """A company not saved yet has no id: its table must not show the
        rates of the active company."""
        industry = self.annex2.with_company(self.company_sn).with_context(
            simplified_tax_company_id=False
        )
        self.assertEqual(industry.current_range_id.name, "Faixa 1")

    def test_company_rates_table_above_the_last_range(self):
        self.company_sn.annual_revenue = 5000000.0
        industry = self._rates_of(self.company_sn, self.annex2)
        self.assertFalse(industry.current_range_id)
        self.assertEqual(industry.current_effective_tax, 0.0)
        self.assertEqual(industry.tax_icms_percent, 0.0)

    # Annex of the main activity of the company

    def test_main_activity_annex(self):
        """The furniture CNAE of the demo company is an industry one."""
        self.assertEqual(self.company_sn.simplified_tax_id, self.annex2)
        self.assertEqual(
            self.company_sn.simplified_tax_range_id,
            self.env.ref("l10n_br_fiscal.simplefied_tax_anexo2_range4"),
        )

    def test_main_activity_annex_r_factor(self):
        """A service CNAE of both the Annex III and the Annex V follows the R
        factor: Annex III from 28% on (LC 123/2006, art. 18, § 5º-J)."""
        cnae = (self.annex3.cnae_ids & self.annex5.cnae_ids)[:1]
        self.company_sn.write(
            {
                "cnae_main_id": cnae.id,
                "annual_revenue": 1000000.0,
                "payroll_amount": 280000.0,
            }
        )
        self.assertTrue(self.company_sn.coefficient_r)
        self.assertEqual(self.company_sn.simplified_tax_id, self.annex3)
        self.company_sn.payroll_amount = 279000.0
        self.assertFalse(self.company_sn.coefficient_r)
        self.assertEqual(self.company_sn.simplified_tax_id, self.annex5)

    def test_main_activity_annex_ignores_r_factor_for_goods(self):
        """The R factor only tells the Annex III from the Annex V: an industry
        with a large payroll keeps the Annex II."""
        self.company_sn.payroll_amount = 400000.0
        self.assertTrue(self.company_sn.coefficient_r)
        self.assertEqual(self.company_sn.simplified_tax_id, self.annex2)

    def test_main_activity_annex_of_cnae_in_two_annexes(self):
        """5620-1/02 is listed both in the Annex I and in the Annex V."""
        self.company_sn.cnae_main_id = self.env.ref("l10n_br_fiscal.cnae_5620102")
        self.assertEqual(len(self.company_sn.simplified_tax_id), 1)

    def test_main_activity_annex_follows_partner_cnae(self):
        """The main CNAE of the company mirrors the one of its partner, with no
        dependency declared by the core: changing it on the partner must still
        recompute the annex."""
        self.assertEqual(self.company_sn.cnae_main_id.code, "3101-2/00")
        cnae = (self.annex4.cnae_ids - self.annex5.cnae_ids)[:1]
        self.company_sn.partner_id.cnae_main_id = cnae
        self.assertEqual(self.company_sn.simplified_tax_id, self.annex4)

    def test_main_activity_range_follows_revenue(self):
        self.company_sn.annual_revenue = 5000000.0
        self.assertEqual(self.company_sn.simplified_tax_id, self.annex2)
        self.assertFalse(self.company_sn.simplified_tax_range_id)
        self.company_sn.annual_revenue = 0.0
        self.assertEqual(
            self.company_sn.simplified_tax_range_id,
            self.env.ref("l10n_br_fiscal.simplefied_tax_anexo2_range1"),
        )

    def test_operation_without_cfop_uses_main_activity_annex(self):
        """Without CFOP, as for services, the annex of the main activity
        applies, while goods keep following their CFOP."""
        cnae = (self.annex4.cnae_ids - self.annex5.cnae_ids)[:1]
        self.company_sn.cnae_main_id = cnae
        no_cfop = self.env["l10n_br_fiscal.cfop"]
        self.assertEqual(self.company_sn._get_simplified_tax(no_cfop), self.annex4)
        self.assertEqual(
            self.company_sn._get_simplified_tax(self.cfop_commerce), self.annex1
        )
