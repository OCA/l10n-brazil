# Copyright 2026 Claudio Noronha - Zaion Solutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged

from ..constants.fiscal import TAX_FRAMEWORK_NORMAL, TAX_FRAMEWORK_SIMPLES


@tagged("post_install", "-at_install")
class TestCompanyTaxDomain(TransactionCase):
    """Test computed domain fields on res.company.

    In Odoo 18, Many2one field domains are evaluated server-side (SQL/Python).
    The view previously used parent.tax_framework which was resolved client-side
    in Odoo <=17.  These tests ensure the computed fields return the correct
    domains so the PIS/COFINS, IPI and ICMS dropdowns filter properly.

    Note: fields.Json round-trips through JSON, so domain leaves are stored as
    lists, not tuples.  Assertions must compare against lists accordingly.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.sn_piscofins = cls.env.ref("l10n_br_fiscal.tax_pis_cofins_simples_nacional")
        cls.ipi_outros = cls.env.ref("l10n_br_fiscal.tax_ipi_outros")
        cls.tax_group_icms = cls.env.ref("l10n_br_fiscal.tax_group_icms")
        cls.tax_group_icmssn = cls.env.ref("l10n_br_fiscal.tax_group_icmssn")

    def test_piscofins_domain_regime_normal(self):
        """Regime Normal: exclude Simples Nacional PIS/COFINS group."""
        self.company.tax_framework = TAX_FRAMEWORK_NORMAL
        domain = self.company.piscofins_id_domain
        self.assertIn(["piscofins_type", "=", "company"], domain)
        self.assertIn(["id", "!=", self.sn_piscofins.id], domain)
        # Simples Nacional group must NOT appear in search results
        results_ids = [
            r[0]
            for r in self.env["l10n_br_fiscal.tax.pis.cofins"].name_search(
                "", domain=domain
            )
        ]
        self.assertNotIn(self.sn_piscofins.id, results_ids)

    def test_piscofins_domain_simples_nacional(self):
        """Simples Nacional: show only the Simples Nacional PIS/COFINS group."""
        self.company.tax_framework = TAX_FRAMEWORK_SIMPLES
        domain = self.company.piscofins_id_domain
        self.assertIn(["piscofins_type", "=", "company"], domain)
        self.assertIn(["id", "=", self.sn_piscofins.id], domain)
        results_ids = [
            r[0]
            for r in self.env["l10n_br_fiscal.tax.pis.cofins"].name_search(
                "", domain=domain
            )
        ]
        self.assertIn(self.sn_piscofins.id, results_ids)
        self.assertEqual(len(results_ids), 1)

    def test_ipi_domain_regime_normal(self):
        """Regime Normal: IPI group must exclude tax_ipi_outros."""
        self.company.tax_framework = TAX_FRAMEWORK_NORMAL
        domain = self.company.tax_ipi_id_domain
        self.assertIn(["id", "!=", self.ipi_outros.id], domain)

    def test_ipi_domain_simples_nacional(self):
        """Simples Nacional: only tax_ipi_outros is valid."""
        self.company.tax_framework = TAX_FRAMEWORK_SIMPLES
        domain = self.company.tax_ipi_id_domain
        self.assertIn(["id", "=", self.ipi_outros.id], domain)

    def test_icms_domain_regime_normal(self):
        """Regime Normal: ICMS domain uses regular tax_group_icms."""
        self.company.tax_framework = TAX_FRAMEWORK_NORMAL
        domain = self.company.tax_icms_id_domain
        self.assertIn(["tax_group_id", "=", self.tax_group_icms.id], domain)
        self.assertNotIn(["tax_group_id", "=", self.tax_group_icmssn.id], domain)

    def test_icms_domain_simples_nacional(self):
        """Simples Nacional: ICMS domain uses tax_group_icmssn."""
        self.company.tax_framework = TAX_FRAMEWORK_SIMPLES
        domain = self.company.tax_icms_id_domain
        self.assertIn(["tax_group_id", "=", self.tax_group_icmssn.id], domain)
        self.assertNotIn(["tax_group_id", "=", self.tax_group_icms.id], domain)
