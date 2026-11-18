# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRtcSimplesNacional(TransactionCase):
    """Simples Nacional: own rates, own matrices (NT 2026.005)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls.env["l10n_br_fiscal.rtc.engine"]
        cls.p_ibs = 1.25
        cls.p_cbs = 2.75

    def _compute(self, cclass, base=1000.0, crt="1", day=None, **kwargs):
        return self.engine.compute_simples_nacional(
            cclass=cclass,
            base=base,
            crt=crt,
            date=day or date(2027, 3, 10),
            p_ibs=self.p_ibs,
            p_cbs=self.p_cbs,
            activity_code="01",
            **kwargs,
        )

    def test_internal_revenue(self):
        result = self._compute("000001")
        self.assertEqual(result["status"], "calculated")
        self.assertEqual(result["revenue_type"], 1)
        self.assertAlmostEqual(result["revenue"], 1000.00, 2)
        self.assertAlmostEqual(result["ibs"]["due"], 12.50, 2)
        self.assertAlmostEqual(result["cbs"]["due"], 27.50, 2)
        self.assertAlmostEqual(result["total"], 40.00, 2)
        self.assertEqual(result["annex"], "I")

    def test_revenue_type_without_calculation(self):
        """tpRBSN 2: revenue exists, but no IBS/CBS is computed."""
        result = self._compute("410008")
        self.assertEqual(result["status"], "calculated")
        self.assertAlmostEqual(result["revenue"], 1000.00, 2)
        self.assertAlmostEqual(result["ibs"]["due"], 0.0, 2)
        self.assertAlmostEqual(result["cbs"]["due"], 0.0, 2)

    def test_half_revenue(self):
        """tpRBSN 5: half of the revenue is taxed (internal + export)."""
        result = self._compute("222001")
        self.assertAlmostEqual(result["revenue"], 1000.00, 2)
        self.assertAlmostEqual(result["base"], 500.00, 2)
        self.assertAlmostEqual(result["ibs"]["due"], 6.25, 2)
        self.assertAlmostEqual(result["cbs"]["due"], 13.75, 2)

    def test_indirect_export_is_pending(self):
        """tpRBSN 4: the value is pending/suspended, not due."""
        result = self._compute("550001")
        self.assertAlmostEqual(result["ibs"]["due"], 0.0, 2)
        self.assertAlmostEqual(result["cbs"]["due"], 0.0, 2)
        self.assertAlmostEqual(result["ibs"]["pending"], 12.50, 2)
        self.assertAlmostEqual(result["cbs"]["pending"], 27.50, 2)

    def test_crt_three_everything_pending(self):
        """CRT=3: even a normal operation is pending/suspended."""
        result = self._compute("000001", crt="3")
        self.assertAlmostEqual(result["ibs"]["due"], 0.0, 2)
        self.assertAlmostEqual(result["cbs"]["due"], 0.0, 2)
        self.assertAlmostEqual(result["ibs"]["pending"], 12.50, 2)

    def test_crt_two_has_no_ibs(self):
        """CRT=2: the IBS is declared by the issuer outside the event."""
        result = self._compute("000001", crt="2")
        self.assertFalse(result["generates_ibs"])
        self.assertAlmostEqual(result["ibs"]["due"], 0.0, 2)
        self.assertAlmostEqual(result["cbs"]["due"], 27.50, 2)

    def test_union_public_purchase_shifts_everything_to_cbs(self):
        result = self._compute("000001", gov_entity_type=1)
        self.assertAlmostEqual(result["p_ibs"], 0.0, 4)
        self.assertAlmostEqual(result["p_cbs"], 4.00, 4)
        self.assertAlmostEqual(result["ibs"]["due"], 0.0, 2)
        self.assertAlmostEqual(result["cbs"]["due"], 40.00, 2)

    def test_state_public_purchase_transition(self):
        """tpEnteGov 2/3/4: 10% of the CBS moves to the IBS in 2029."""
        result = self._compute("000001", day=date(2029, 6, 1), gov_entity_type=2)
        self.assertAlmostEqual(result["p_ibs"], 1.25 + 0.275, 4)
        self.assertAlmostEqual(result["p_cbs"], 2.475, 4)

    def test_missing_activity_is_not_an_error(self):
        result = self.engine.compute_simples_nacional(
            cclass="000001",
            base=1000.0,
            crt="1",
            date=date(2027, 3, 10),
            p_ibs=self.p_ibs,
            p_cbs=self.p_cbs,
        )
        self.assertEqual(result["status"], "not_calculated")

    def test_unknown_classification(self):
        result = self._compute("999999")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["errors"][0]["code"], "RTC-101")

    def test_tables(self):
        activity = self.env["l10n_br_fiscal.rtc.sn.activity"].find(
            "01", date(2027, 3, 10)
        )
        self.assertEqual(activity.annex, "I")
        regime = self.env["l10n_br_fiscal.rtc.sn.regime"].find("3", date(2027, 3, 10))
        self.assertEqual(regime.destination_due, "PENDENTE_SUSPENSO")
        self.assertEqual(regime.destination_pending, "ZERO")
        transition = self.env["l10n_br_fiscal.rtc.sn.transition"].find(date(2030, 6, 1))
        self.assertAlmostEqual(transition.factor, 0.2, 4)
