# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestDctfwebAssessment(AccountTestInvoicingCommon):
    """The MIT confesses what the tax assessment already persisted."""

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company = cls.company_data["company"]
        cls.company.write(
            {
                "cnpj_cpf": "12.345.678/0001-95",
                "dctfweb_pj_qualification": "1",
                "dctfweb_profit_taxation": "3",
                "dctfweb_monetary_variation": "2",
                "dctfweb_pis_cofins_regime": "2",
                "dctfweb_responsible_cpf": "07206845000",
            }
        )
        cls.code_pis = cls.env.ref("l10n_br_dctfweb.revenue_code_810902")
        cls.code_cofins = cls.env.ref("l10n_br_dctfweb.revenue_code_217201")
        cls.code_ipi = cls.env.ref("l10n_br_dctfweb.revenue_code_066803")

    def _tax_group(self, name, code, regime="cumulative"):
        return self.env["account.tax.group"].create(
            {
                "name": name,
                "regime": regime,
                "dctfweb_revenue_code_id": code and code.id or False,
            }
        )

    def _tax_assessment(self, group, amount, date_from=None, date_to=None):
        """A persisted assessment whose assessed balance is ``amount``."""
        assessment = self.env["l10n_br_tax.assessment"].create(
            {
                "company_id": self.company.id,
                "tax_group_id": group.id,
                "date_from": date_from or "2026-07-01",
                "date_to": date_to or "2026-07-31",
            }
        )
        self.env["l10n_br_tax.assessment.line"].create(
            {
                "assessment_id": assessment.id,
                "kind": "debit",
                "source": "manual",
                "description": "Test",
                "tax_amount": amount,
            }
        )
        assessment.state = "computed"
        return assessment

    def _mit(self, **values):
        base = {
            "company_id": self.company.id,
            "year": 2026,
            "month": "7",
        }
        base.update(values)
        return self.env["l10n_br_dctfweb.assessment"].create(base)

    # ------------------------------------------------------------------

    def test_the_period_is_the_month(self):
        mit = self._mit()
        self.assertEqual(str(mit.date_from), "2026-07-01")
        self.assertEqual(str(mit.date_to), "2026-07-31")
        self.assertEqual(mit.name, "MIT 07/2026")

    def test_the_company_defaults_fill_the_initial_data(self):
        """The accountant should not retype the qualification every month."""
        mit = self._mit()
        self.assertEqual(mit.pj_qualification, "1")
        self.assertEqual(mit.profit_taxation, "3")
        self.assertEqual(mit.responsible_cpf, "07206845000")

    def test_a_period_before_2025_is_refused(self):
        with self.assertRaises(UserError):
            self._mit(year=2024)

    def test_assessing_reads_the_persisted_assessment(self):
        group = self._tax_group("PIS cumulative", self.code_pis)
        self._tax_assessment(group, 1000.0)
        mit = self._mit()
        mit.action_assess()
        self.assertEqual(mit.state, "assessed")
        self.assertEqual(len(mit.debit_ids), 1)
        debit = mit.debit_ids
        self.assertEqual(debit.revenue_code_id, self.code_pis)
        self.assertEqual(debit.amount, 1000.0)
        self.assertEqual(debit.source, "computed")

    def test_the_confessed_amount_is_the_assessed_balance(self):
        """Withholding does not shrink the confession: it is matched later.

        The tax assessment reduces ``amount_payable`` by the withholding, but
        the MIT confesses the debit itself, field 11 of the E110.
        """
        group = self._tax_group("PIS cumulative", self.code_pis)
        assessment = self._tax_assessment(group, 1000.0)
        self.env["l10n_br_tax.assessment.line"].create(
            {
                "assessment_id": assessment.id,
                "kind": "withholding",
                "source": "manual",
                "description": "Withheld at source",
                "tax_amount": 150.0,
            }
        )
        self.assertEqual(assessment.amount_payable, 850.0)
        self.assertEqual(assessment.assessed_balance, 1000.0)
        mit = self._mit()
        mit.action_assess()
        self.assertEqual(mit.debit_ids.amount, 1000.0)

    def test_a_group_without_revenue_code_is_skipped_and_logged(self):
        """ICMS is not confessed in the MIT, and silence would be a trap."""
        group = self._tax_group("ICMS", None)
        self._tax_assessment(group, 500.0)
        mit = self._mit()
        mit.action_assess()
        self.assertFalse(mit.debit_ids)
        self.assertTrue(any("ICMS" in str(message.body) for message in mit.message_ids))

    def test_an_assessment_of_another_month_is_not_read(self):
        group = self._tax_group("PIS cumulative", self.code_pis)
        self._tax_assessment(group, 700.0, date_from="2026-06-01", date_to="2026-06-30")
        mit = self._mit()
        mit.action_assess()
        self.assertFalse(mit.debit_ids)

    def test_a_draft_tax_assessment_is_not_read(self):
        group = self._tax_group("PIS cumulative", self.code_pis)
        assessment = self._tax_assessment(group, 700.0)
        assessment.state = "draft"
        mit = self._mit()
        mit.action_assess()
        self.assertFalse(mit.debit_ids)

    def test_two_regimes_of_the_same_tax_become_two_debits(self):
        """A mixed taxpayer confesses PIS twice, under two revenue codes."""
        cumulative = self._tax_group("PIS cumulative", self.code_pis, "cumulative")
        non_cumulative = self._tax_group(
            "PIS non cumulative",
            self.env.ref("l10n_br_dctfweb.revenue_code_691201"),
            "non_cumulative",
        )
        self._tax_assessment(cumulative, 300.0)
        self._tax_assessment(non_cumulative, 400.0)
        mit = self._mit()
        mit.action_assess()
        self.assertEqual(len(mit.debit_ids), 2)
        self.assertEqual(mit.debit_total, 700.0)
        self.assertEqual(
            set(mit.debit_ids.mapped("revenue_code_id.mit_code")),
            {"810902", "691201"},
        )

    def test_assessing_again_keeps_the_manual_debits(self):
        group = self._tax_group("PIS cumulative", self.code_pis)
        self._tax_assessment(group, 1000.0)
        mit = self._mit()
        mit.action_assess()
        self.env["l10n_br_dctfweb.debit"].create(
            {
                "assessment_id": mit.id,
                "revenue_code_id": self.code_cofins.id,
                "amount": 55.0,
                "source": "manual",
            }
        )
        mit.action_assess()
        self.assertEqual(len(mit.debit_ids), 2)
        self.assertEqual(len(mit.debit_ids.filtered(lambda d: d.source == "manual")), 1)

    def test_the_ipi_debit_carries_the_establishment(self):
        group = self._tax_group("IPI", self.code_ipi, "not_applicable")
        self._tax_assessment(group, 220.0)
        mit = self._mit()
        mit.action_assess()
        self.assertEqual(mit.debit_ids.establishment_cnpj, "000195")

    def test_debit_numbers_are_sequential(self):
        group = self._tax_group("PIS cumulative", self.code_pis)
        other = self._tax_group("COFINS cumulative", self.code_cofins)
        self._tax_assessment(group, 100.0)
        self._tax_assessment(other, 200.0)
        mit = self._mit()
        mit.action_assess()
        self.assertEqual(sorted(mit.debit_ids.mapped("debit_number")), [1, 2])

    # ------------------------------------------------------------------
    # Pendencies, the manual's item 3.6
    # ------------------------------------------------------------------

    def test_an_assessment_with_movement_needs_a_debit(self):
        mit = self._mit()
        mit.action_assess()
        with self.assertRaises(UserError):
            mit.action_close()

    def test_without_the_responsible_cpf_it_does_not_close(self):
        group = self._tax_group("PIS cumulative", self.code_pis)
        self._tax_assessment(group, 100.0)
        mit = self._mit(responsible_cpf=False)
        mit.action_assess()
        with self.assertRaises(UserError):
            mit.action_close()

    def test_a_short_cpf_does_not_close(self):
        group = self._tax_group("PIS cumulative", self.code_pis)
        self._tax_assessment(group, 100.0)
        mit = self._mit(responsible_cpf="123")
        mit.action_assess()
        with self.assertRaises(UserError):
            mit.action_close()

    def test_an_ipi_debit_without_establishment_does_not_close(self):
        mit = self._mit()
        self.env["l10n_br_dctfweb.debit"].create(
            {
                "assessment_id": mit.id,
                "revenue_code_id": self.code_ipi.id,
                "amount": 10.0,
            }
        )
        mit.action_assess()
        pendencies = mit._check_pendencies()
        self.assertTrue(
            any("establishment" in pendency for pendency in pendencies), pendencies
        )

    def test_a_ten_day_debit_without_period_does_not_close(self):
        mit = self._mit()
        self.env["l10n_br_dctfweb.debit"].create(
            {
                "assessment_id": mit.id,
                "revenue_code_id": self.env.ref(
                    "l10n_br_dctfweb.revenue_code_402802"
                ).id,
                "amount": 10.0,
            }
        )
        pendencies = mit._check_pendencies()
        self.assertTrue(
            any("period of the debit" in pendency for pendency in pendencies),
            pendencies,
        )

    def test_a_ten_day_period_above_three_does_not_close(self):
        mit = self._mit()
        self.env["l10n_br_dctfweb.debit"].create(
            {
                "assessment_id": mit.id,
                "revenue_code_id": self.env.ref(
                    "l10n_br_dctfweb.revenue_code_402802"
                ).id,
                "amount": 10.0,
                "period": 7,
                "gold_city_id": self.env["res.city"]
                .search([("country_id.code", "=", "BR")], limit=1)
                .id,
            }
        )
        pendencies = mit._check_pendencies()
        self.assertTrue(
            any("between 1 and 3" in pendency for pendency in pendencies), pendencies
        )

    def test_closing_freezes_the_file(self):
        group = self._tax_group("PIS cumulative", self.code_pis)
        self._tax_assessment(group, 1000.0)
        mit = self._mit()
        mit.action_assess()
        mit.action_close()
        self.assertEqual(mit.state, "closed")
        self.assertEqual(mit.mit_filename, "12345678-MIT-202607.json")
        self.assertTrue(mit.mit_file)

    def test_closing_requires_the_assessment_first(self):
        mit = self._mit()
        with self.assertRaises(UserError):
            mit.action_close()

    # ------------------------------------------------------------------
    # Without movement
    # ------------------------------------------------------------------

    def test_an_assessment_without_movement_closes_with_no_debit(self):
        mit = self._mit(no_movement=True)
        mit.action_assess()
        mit.action_close()
        self.assertEqual(mit.state, "closed")
        self.assertFalse(mit.debit_ids)

    def test_without_movement_it_does_not_read_the_tax_assessment(self):
        group = self._tax_group("PIS cumulative", self.code_pis)
        self._tax_assessment(group, 1000.0)
        mit = self._mit(no_movement=True)
        mit.action_assess()
        self.assertFalse(mit.debit_ids)
        self.assertFalse(mit.tax_assessment_ids)

    def test_without_movement_a_debit_is_a_pendency(self):
        mit = self._mit(no_movement=True)
        self.env["l10n_br_dctfweb.debit"].create(
            {
                "assessment_id": mit.id,
                "revenue_code_id": self.code_pis.id,
                "amount": 10.0,
            }
        )
        mit.state = "assessed"
        with self.assertRaises(UserError):
            mit.action_close()

    # ------------------------------------------------------------------
    # Rectification
    # ------------------------------------------------------------------

    def test_the_same_period_cannot_be_declared_twice(self):
        from psycopg2 import IntegrityError

        from odoo.tools import mute_logger

        self._mit()
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self._mit()
            self.env.flush_all()

    def test_only_a_transmitted_assessment_is_rectified(self):
        mit = self._mit()
        with self.assertRaises(UserError):
            mit.action_rectify()

    def test_a_rectification_is_a_new_assessment_of_the_same_period(self):
        group = self._tax_group("PIS cumulative", self.code_pis)
        self._tax_assessment(group, 1000.0)
        mit = self._mit()
        mit.action_assess()
        mit.action_close()
        mit.state = "transmitted"
        action = mit.action_rectify()
        rectification = self.env["l10n_br_dctfweb.assessment"].browse(action["res_id"])
        self.assertEqual(rectification.rectification_of_id, mit)
        self.assertEqual(rectification.rectification_sequence, 1)
        self.assertEqual(rectification.state, "draft")
        self.assertEqual(rectification.year, mit.year)
        self.assertEqual(rectification.month, mit.month)
        self.assertEqual(rectification.name, "MIT 07/2026 (1)")

    def test_a_transmitted_assessment_does_not_go_back_to_draft(self):
        mit = self._mit()
        mit.state = "transmitted"
        with self.assertRaises(UserError):
            mit.action_draft()
