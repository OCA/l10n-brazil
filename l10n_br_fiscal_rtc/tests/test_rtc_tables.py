# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRtcTables(TransactionCase):
    """Guard the generated data: a truncated sync must break the build."""

    def test_treatments(self):
        treatments = self.env["l10n_br_fiscal.rtc.treatment"].search([])
        self.assertGreaterEqual(len(treatments), 43)
        general = treatments.filtered(lambda t: t.code == 3)
        self.assertEqual(len(general), 1)
        self.assertIn("aliquota", general.expr_effective_rate)
        self.assertIn("percentualReducao", general.expr_effective_rate)

    def test_legal_basis(self):
        basis = self.env["l10n_br_fiscal.rtc.legal.basis"].search([])
        self.assertGreaterEqual(len(basis), 169)
        self.assertTrue(all(record.normative_reference for record in basis))

    def test_official_rates_2026(self):
        rates = self.env["l10n_br_fiscal.rtc.rate"]
        self.assertGreaterEqual(len(rates.search([])), 3)
        self.assertAlmostEqual(float(rates.get_rate("cbs", date(2026, 6, 1))), 0.9, 4)
        self.assertAlmostEqual(
            float(rates.get_rate("ibs_uf", date(2026, 6, 1))), 0.1, 4
        )
        self.assertAlmostEqual(
            float(rates.get_rate("ibs_mun", date(2026, 6, 1))), 0.0, 4
        )

    def test_classification_full_reduction(self):
        """200003 (cesta básica) is taxed at zero through a 100% reduction."""
        classification = self.env["l10n_br_fiscal.tax.classification"].search(
            [("code", "=", "200003")], limit=1
        )
        self.assertTrue(classification)
        self.assertEqual(classification.rtc_treatment_id.code, 9)
        self.assertEqual(classification.rtc_reduction_cbs, 100)
        self.assertEqual(classification.rtc_reduction_ibs_uf, 100)
        self.assertEqual(classification.rtc_nomenclature, "ncm")

    def test_classification_standard(self):
        classification = self.env["l10n_br_fiscal.tax.classification"].search(
            [("code", "=", "000001")], limit=1
        )
        self.assertTrue(classification)
        self.assertEqual(classification.rtc_treatment_id.code, 3)
        self.assertEqual(classification.rtc_reduction_cbs, 0)
        self.assertTrue(classification.rtc_credit_acquirer_ibs)
        self.assertTrue(classification.rtc_credit_acquirer_cbs)
        self.assertEqual(classification.rtc_prior_credit, "maintain")
        self.assertTrue(classification.rtc_legal_basis_id)

    def test_every_classification_has_a_treatment(self):
        classifications = self.env["l10n_br_fiscal.tax.classification"].search(
            [("rtc_treatment_id", "!=", False)]
        )
        self.assertGreaterEqual(len(classifications), 150)
        self.assertFalse(
            classifications.filtered(lambda c: not c.rtc_treatment_id.expr_base)
        )

    def test_nomenclature(self):
        nomenclature = self.env["l10n_br_fiscal.rtc.nomenclature"]
        self.assertGreaterEqual(len(nomenclature.search([])), 1200)
        self.assertTrue(
            nomenclature.is_applicable("200003", "10063021", "ncm", date(2026, 6, 1))
        )
        self.assertFalse(
            nomenclature.is_applicable("200035", "02013000", "ncm", date(2026, 6, 1))
        )
