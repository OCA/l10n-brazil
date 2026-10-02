# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestAssessmentDeadlines(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.period_model = cls.env["l10n_br_assessment.period"]

    def _create_period(self, per_apur="2026-10"):
        return self.period_model.create(
            {
                "company_id": self.company.id,
                "tribute": "cbs",
                "per_apur": per_apur,
            }
        )

    def test_period_dates(self):
        period = self._create_period("2026-02")
        self.assertEqual(period.date_from, date(2026, 2, 1))
        self.assertEqual(period.date_to, date(2026, 2, 28))
        self.assertEqual(period.name, "CBS 2026-02")

    def test_invalid_per_apur(self):
        with self.assertRaises(ValidationError):
            self._create_period("2026-13")

    def test_availability_day_without_dere(self):
        self.company.assessment_dere_subject = False
        self.assertEqual(self._create_period().date_available, date(2026, 11, 15))

    def test_availability_day_with_dere(self):
        self.company.assessment_dere_subject = True
        self.assertEqual(self._create_period().date_available, date(2026, 11, 20))

    def test_deadline_is_last_business_day(self):
        # November 2026 ends on Monday the 30th.
        self.assertEqual(
            self._create_period("2026-10").date_deadline, date(2026, 11, 30)
        )
        # January 2027 ends on Sunday the 31st, so the deadline moves to Friday.
        self.assertEqual(
            self._create_period("2026-12").date_deadline, date(2027, 1, 29)
        )

    def test_deadline_skips_holiday(self):
        calendar = self.env["resource.calendar"].create({"name": "Head office"})
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Municipal holiday",
                "calendar_id": calendar.id,
                "leave_type": "F",
                "date_from": "2026-11-30 00:00:00",
                "date_to": "2026-11-30 23:59:59",
            }
        )
        self.company.assessment_calendar_id = calendar
        self.assertEqual(self._create_period().date_deadline, date(2026, 11, 27))

    def test_expires_period_after_deadline(self):
        period = self._create_period()
        period.state = "received"
        self.period_model._check_deadlines(period.date_deadline + timedelta(days=1))
        self.assertEqual(period.state, "expired")

    def test_confirmed_period_is_never_expired(self):
        period = self._create_period()
        period.state = "confirmed"
        self.period_model._check_deadlines(period.date_deadline + timedelta(days=1))
        self.assertEqual(period.state, "confirmed")

    def test_schedules_a_single_activity_near_deadline(self):
        period = self._create_period()
        period.state = "received"
        near_deadline = period.date_deadline - timedelta(days=2)
        self.period_model._check_deadlines(near_deadline)
        self.period_model._check_deadlines(near_deadline)
        activities = period.activity_ids.filtered(
            lambda act: act.summary
            == f"Review the assisted assessment of {period.name}"
        )
        self.assertEqual(len(activities), 1)
        self.assertEqual(period.state, "received")
