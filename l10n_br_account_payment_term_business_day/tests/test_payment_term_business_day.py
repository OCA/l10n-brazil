# Copyright (C) 2026 - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import date, datetime

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPaymentTermBusinessDay(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar = cls.env["resource.calendar"].create({"name": "Brasil"})
        # 2026-09-07, Independence Day, falls on a Monday.
        cls.env["resource.calendar.leaves"].create(
            {
                "name": "Independence Day",
                "date_from": datetime(2026, 9, 7, 0, 0),
                "date_to": datetime(2026, 9, 7, 23, 59),
                "leave_type": "F",
                "calendar_id": cls.calendar.id,
            }
        )
        cls.company = cls.env.company
        cls.currency = cls.company.currency_id

    def _term(self, policy, calendar=None, days=0):
        term = self.env["account.payment.term"].create(
            {
                "name": f"Term {policy}",
                "business_day_policy": policy,
                "holiday_calendar_id": (
                    calendar.id if calendar is not None else self.calendar.id
                ),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "percent",
                            "value_amount": 100.0,
                            "delay_type": "days_after",
                            "nb_days": days,
                        },
                    )
                ],
            }
        )
        return term

    def _due_dates(self, term, date_ref):
        result = term._compute_terms(
            date_ref=date_ref,
            currency=self.currency,
            company=self.company,
            tax_amount=0.0,
            tax_amount_currency=0.0,
            sign=1,
            untaxed_amount=100.0,
            untaxed_amount_currency=100.0,
        )
        return [line["date"] for line in result["line_ids"]]

    def test_holiday_postpones_to_the_next_banking_day(self):
        term = self._term("next")
        # A due date on Monday 2026-09-07, a holiday, moves to Tuesday the 8th
        self.assertEqual(self._due_dates(term, date(2026, 9, 7)), [date(2026, 9, 8)])

    def test_holiday_anticipates_to_the_previous_banking_day(self):
        term = self._term("previous")
        # Same date, opposite direction: Friday 2026-09-04
        self.assertEqual(self._due_dates(term, date(2026, 9, 7)), [date(2026, 9, 4)])

    def test_weekend_moves_even_without_a_holiday(self):
        term = self._term("next")
        # 2026-09-05 is a Saturday
        self.assertEqual(self._due_dates(term, date(2026, 9, 5)), [date(2026, 9, 8)])

    def test_a_banking_day_is_left_untouched(self):
        """next_bank_business_day is strictly after: without normalizing first,
        a date that already settles would be pushed a day for no reason."""
        for policy in ("next", "previous"):
            term = self._term(policy)
            self.assertEqual(
                self._due_dates(term, date(2026, 9, 9)), [date(2026, 9, 9)]
            )

    def test_bank_only_holiday_moves_the_due_date(self):
        """Carnival is a working day and settles nothing at a bank."""
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Carnaval",
                "date_from": datetime(2026, 2, 17, 0, 0),
                "date_to": datetime(2026, 2, 17, 23, 59),
                "leave_type": "B",
                "calendar_id": self.calendar.id,
            }
        )
        term = self._term("next")
        self.assertNotEqual(
            self._due_dates(term, date(2026, 2, 17)), [date(2026, 2, 17)]
        )

    def test_policy_none_keeps_the_standard_behaviour(self):
        term = self._term("none", calendar=self.env["resource.calendar"])
        self.assertEqual(self._due_dates(term, date(2026, 9, 7)), [date(2026, 9, 7)])

    def test_every_instalment_is_shifted(self):
        term = self.env["account.payment.term"].create(
            {
                "name": "30/60",
                "business_day_policy": "previous",
                "holiday_calendar_id": self.calendar.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "percent",
                            "value_amount": 50.0,
                            "delay_type": "days_after",
                            "nb_days": 0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "value": "percent",
                            "value_amount": 50.0,
                            "delay_type": "days_after",
                            "nb_days": 2,
                        },
                    ),
                ],
            }
        )
        # 2026-09-05 is a Saturday and 09-07 a holiday: both instalments move back
        vencimentos = self._due_dates(term, date(2026, 9, 5))
        self.assertEqual(vencimentos, [date(2026, 9, 4), date(2026, 9, 4)])

    def test_shift_without_a_calendar_is_refused(self):
        """Without a calendar only weekends would be skipped and a holiday would
        pass as a valid due date: a silent failure that turns into a fine."""
        with self.assertRaises(ValidationError):
            self.env["account.payment.term"].create(
                {
                    "name": "No calendar",
                    "business_day_policy": "next",
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "value": "percent",
                                "value_amount": 100.0,
                                "delay_type": "days_after",
                            },
                        )
                    ],
                }
            )

    def test_municipal_holiday_only_moves_its_own_calendar(self):
        """ISS is municipal: a decree in one city does not move a due date in
        another. The child calendar inherits the national holidays and adds its own."""
        indaiatuba = self.env["resource.calendar"].create(
            {"name": "Indaiatuba", "parent_id": self.calendar.id}
        )
        self.env["resource.calendar.leaves"].create(
            {
                "name": "City anniversary",
                "date_from": datetime(2026, 12, 9, 0, 0),
                "date_to": datetime(2026, 12, 9, 23, 59),
                "leave_type": "F",
                "calendar_id": indaiatuba.id,
            }
        )
        local = self._term("previous", calendar=indaiatuba)
        nacional = self._term("previous")
        self.assertEqual(self._due_dates(local, date(2026, 12, 9)), [date(2026, 12, 8)])
        self.assertEqual(
            self._due_dates(nacional, date(2026, 12, 9)), [date(2026, 12, 9)]
        )
