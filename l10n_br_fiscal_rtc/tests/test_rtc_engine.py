# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date
from decimal import Decimal

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRtcEngine(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls.env["l10n_br_fiscal.rtc.engine"]
        cls.state_rs = cls.env["res.country.state"].search(
            [("code", "=", "RS"), ("country_id.code", "=", "BR")], limit=1
        )
        # Nominal rates of the 2027 example of the official documentation.
        cls.rates_2027 = {"cbs": 8.8, "ibs_uf": 0.05, "ibs_mun": 0.05}

    def test_documented_case(self):
        """The example of docs/exemplos.md of the official calculator."""
        result = self.engine.compute(
            [
                {"cclass": "200003", "base": 100.0, "quantity": 20},
                {
                    "cclass": "000001",
                    "base": 150.0,
                    "is_calculated": 15.0,
                    "quantity": 12,
                },
                {
                    "cclass": "200028",
                    "base": 1200.0,
                    "nomenclature_code": "122011200",
                },
            ],
            date=date(2027, 3, 10),
            state=self.state_rs,
            rates=self.rates_2027,
        )
        statuses = [item["status"] for item in result["items"]]
        self.assertEqual(statuses, ["calculated"] * 3)
        self.assertAlmostEqual(result["totals"]["base"], 1465.00, 2)
        self.assertAlmostEqual(result["totals"]["cbs"], 56.76, 2)
        self.assertAlmostEqual(result["totals"]["ibs"], 0.64, 2)

    def test_reduced_rate(self):
        """200028 is a 60% reduction: base of the IS is added to the line."""
        item = self.engine.compute_item(
            "200028",
            1200.0,
            date=date(2027, 3, 10),
            state=self.state_rs,
            rates=self.rates_2027,
        )
        self.assertEqual(item["status"], "calculated")
        self.assertAlmostEqual(item["taxes"]["cbs"]["effective_rate"], 3.52, 4)
        self.assertAlmostEqual(item["taxes"]["cbs"]["value"], 42.24, 2)
        self.assertAlmostEqual(item["taxes"]["ibs_uf"]["value"], 0.24, 2)

    def test_zero_rate_treatment(self):
        item = self.engine.compute_item(
            "200003",
            100.0,
            date=date(2027, 3, 10),
            state=self.state_rs,
            rates=self.rates_2027,
        )
        self.assertEqual(item["status"], "calculated")
        self.assertAlmostEqual(item["taxes"]["cbs"]["value"], 0.0, 2)
        self.assertAlmostEqual(item["total"], 0.0, 2)

    def test_rates_from_official_table(self):
        """2026 test year: CBS 0.9%, IBS state 0.1%, IBS municipality 0%."""
        item = self.engine.compute_item(
            "000001", 1000.0, date=date(2026, 6, 1), state=self.state_rs
        )
        self.assertEqual(item["status"], "calculated")
        self.assertAlmostEqual(item["taxes"]["cbs"]["rate"], 0.9, 4)
        self.assertAlmostEqual(item["taxes"]["cbs"]["value"], 9.00, 2)
        self.assertAlmostEqual(item["taxes"]["ibs_uf"]["value"], 1.00, 2)
        self.assertAlmostEqual(item["taxes"]["ibs_mun"]["value"], 0.00, 2)
        self.assertAlmostEqual(item["total"], 10.00, 2)

    def test_missing_rate_is_reported(self):
        """No 2027 rate in the official table yet: reported, never guessed."""
        result = self.engine.compute_item("000001", 1000.0, date=date(2027, 6, 1))
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["errors"][0]["code"], "RTC-007")

    def test_nomenclature_mismatch(self):
        result = self.engine.compute_item(
            "200035",
            80.0,
            date=date(2027, 3, 10),
            state=self.state_rs,
            rates=self.rates_2027,
            nomenclature_code="02013000",
        )
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["errors"][0]["code"], "RTC-011")

    def test_nomenclature_match_uses_prefix(self):
        """Annexes list 4 to 8 digit prefixes: 100630 must cover 10063021."""
        result = self.engine.compute_item(
            "200003",
            100.0,
            date=date(2027, 3, 10),
            state=self.state_rs,
            rates=self.rates_2027,
            nomenclature_code="10063021",
        )
        self.assertEqual(result["status"], "calculated")

    def test_government_reducer(self):
        """pRedutorCompraGov reduces the effective rate, not the nominal one."""
        full = self.engine.compute_item(
            "000001",
            1000.0,
            date=date(2027, 3, 10),
            state=self.state_rs,
            rates=self.rates_2027,
        )
        reduced = self.engine.compute_item(
            "000001",
            1000.0,
            date=date(2027, 3, 10),
            state=self.state_rs,
            rates=self.rates_2027,
            gov_reducer=13.5,
        )
        self.assertAlmostEqual(full["taxes"]["cbs"]["value"], 88.00, 2)
        self.assertAlmostEqual(reduced["taxes"]["cbs"]["value"], 88.00 * (1 - 0.135), 2)

    def test_banker_rounding(self):
        """The official engine uses HALF_EVEN, Odoo defaults to HALF_UP."""
        engine = self.engine
        self.assertEqual(engine._r2(Decimal("0.005")), Decimal("0.00"))
        self.assertEqual(engine._r2(Decimal("0.015")), Decimal("0.02"))
        self.assertEqual(engine._r2(Decimal("0.025")), Decimal("0.02"))

    def test_partial_deferral_is_refused(self):
        """Upstream subtracts a partial deferral twice: refuse instead."""
        treatment = self.env["l10n_br_fiscal.rtc.treatment"].create(
            {
                "code": 999,
                "name": "Partial deferral (test)",
                "expr_rate": "aliquota",
                "expr_effective_rate": "aliquota",
                "expr_base": "baseCalculoInformada",
                "expr_tax_computed": "baseCalculo*aliquotaEfetiva",
                "expr_tax_due": "tributoCalculado",
                "expr_deferral_percent": "0.3",
                "expr_deferral_value": "tributoCalculado*0.3",
                "date_start": "2026-01-01",
            }
        )
        classification = self.env.ref("l10n_br_fiscal.tax_classification_000001")
        classification.rtc_treatment_id = treatment
        result = self.engine.compute_item("000001", 1000.0, date=date(2026, 6, 1))
        self.assertEqual(result["status"], "not_implemented")
        self.assertEqual(result["errors"][0]["code"], "RTC-006")

    def test_unknown_cclass(self):
        result = self.engine.compute_item("999999", 10.0, date=date(2026, 6, 1))
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["errors"][0]["code"], "RTC-001")
