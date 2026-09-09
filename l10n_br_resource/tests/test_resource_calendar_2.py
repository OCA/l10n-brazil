from datetime import date, datetime

from odoo.tests import common


class TestResourceCalendar(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.calendar = self.env["resource.calendar"].create({"name": "Test Calendar"})

        self.env["resource.calendar.leaves"].create(
            {
                "name": "Christmas",
                "date_from": datetime(2023, 12, 25, 0, 0),
                "date_to": datetime(2023, 12, 25, 23, 59),
                "leave_type": "F",
                "calendar_id": self.calendar.id,
            }
        )

    def test_is_holiday(self):
        holiday_date = datetime(2023, 12, 25)
        result = self.calendar.is_holiday(holiday_date)
        expected_result = True
        self.assertEqual(result, expected_result)

        non_holiday_date = datetime(2023, 12, 24)
        result = self.calendar.is_holiday(non_holiday_date)
        expected_result = False
        self.assertEqual(result, expected_result)

        non_holiday_date2 = datetime(2023, 4, 13)
        result = self.calendar.is_holiday(non_holiday_date2)
        expected_result = False
        self.assertEqual(result, expected_result)

        # No date
        self.calendar.is_holiday(False)

    def test_is_bank_holiday(self):
        """The count is scoped to this calendar and its ancestors, not to the whole
        database: another municipality's holiday must not close this calendar."""
        self.assertEqual(self.calendar.is_bank_holiday(datetime(2023, 12, 25)), 1)
        self.assertEqual(self.calendar.is_bank_holiday(datetime(2023, 12, 24)), 0)

        other_calendar = self.env["resource.calendar"].create({"name": "Other City"})
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Local holiday of another city",
                "date_from": datetime(2023, 6, 13, 0, 0),
                "date_to": datetime(2023, 6, 13, 23, 59),
                "leave_type": "F",
                "calendar_id": other_calendar.id,
            }
        )
        self.assertEqual(self.calendar.is_bank_holiday(datetime(2023, 6, 13)), 0)
        self.assertEqual(other_calendar.is_bank_holiday(datetime(2023, 6, 13)), 1)
        # No date
        self.calendar.is_bank_holiday(False)

    def test_is_bank_holiday_inherits_from_the_parent_calendar(self):
        """Country holidays live on the country calendar and must reach the city."""
        city = self.env["resource.calendar"].create(
            {"name": "City", "parent_id": self.calendar.id}
        )
        self.assertEqual(city.is_bank_holiday(datetime(2023, 12, 25)), 1)

    def test_is_bank_holiday_accepts_a_plain_date(self):
        """A date at midnight would fall before a leave stored at 03:00 UTC and report
        a holiday as a working day; the date is normalized to midday."""
        self.assertEqual(self.calendar.is_bank_holiday(date(2023, 12, 25)), 1)

    def test_bank_only_holidays_close_the_banks(self):
        """Carnival and Corpus Christi are leave_type B: not a public holiday, but no
        bank settles on them, which is what a tax due date follows."""
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Carnival",
                "date_from": datetime(2023, 2, 20, 0, 0),
                "date_to": datetime(2023, 2, 21, 23, 59),
                "leave_type": "B",
                "calendar_id": self.calendar.id,
            }
        )
        self.assertEqual(self.calendar.is_bank_holiday(datetime(2023, 2, 20)), 1)
        self.assertFalse(self.calendar.is_bank_business_day(datetime(2023, 2, 20)))

    def test_previous_business_day_walks_backwards(self):
        # 2023-12-25 is a Monday holiday, so the day before is Friday 2023-12-22
        self.assertEqual(
            self.calendar.previous_business_day(datetime(2023, 12, 26)).date(),
            date(2023, 12, 22),
        )

    def test_previous_business_day_is_strictly_before(self):
        """Mirror of next_business_day: a working day is not returned as its own
        previous day, so the caller decides whether to normalize first."""
        friday = datetime(2023, 12, 22)
        self.assertLess(self.calendar.previous_business_day(friday), friday)

    def test_previous_bank_business_day_skips_a_bank_only_holiday(self):
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Corpus Christi",
                "date_from": datetime(2023, 6, 8, 0, 0),
                "date_to": datetime(2023, 6, 8, 23, 59),
                "leave_type": "B",
                "calendar_id": self.calendar.id,
            }
        )
        # Friday 2023-06-09 anticipates over Thursday 08 (bank holiday) to Wednesday 07
        self.assertEqual(
            self.calendar.previous_bank_business_day(datetime(2023, 6, 9)).date(),
            date(2023, 6, 7),
        )

    def test_previous_business_day_crosses_the_weekend(self):
        monday = datetime(2023, 4, 17)
        self.assertEqual(
            self.calendar.previous_business_day(monday).date(), date(2023, 4, 14)
        )

    def test_is_extended_holiday(self):
        reference_date = datetime(2023, 9, 7, 15, 0, 0)
        expected_result = False

        result = self.calendar.is_extended_holiday(reference_date)

        self.assertEqual(result, expected_result)
        # No date
        self.calendar.is_extended_holiday(False)

    def test_is_bank_business_day(self):
        business_date = datetime(2023, 4, 17)
        self.assertTrue(self.calendar.is_bank_business_day(business_date))

        non_business_date = datetime(2023, 4, 15)
        self.assertFalse(self.calendar.is_bank_business_day(non_business_date))

        non_business_date = datetime(2023, 4, 16)
        self.assertFalse(self.calendar.is_bank_business_day(non_business_date))

        holiday_date = datetime(2023, 4, 21)
        self.assertTrue(self.calendar.is_bank_business_day(holiday_date))

    def test_get_base_days_commercial_month(self):
        date_from = datetime(2023, 4, 1)
        date_to = datetime(2023, 4, 30)
        self.assertEqual(self.calendar.get_base_days(date_from, date_to, True), 30)

        date_from = datetime(2023, 4, 15)
        date_to = datetime(2023, 4, 30)
        self.assertEqual(self.calendar.get_base_days(date_from, date_to, True), 16)

    def test_get_base_days_non_commercial_month(self):
        date_from = datetime(2023, 4, 1)
        date_to = datetime(2023, 4, 15)
        self.assertEqual(self.calendar.get_base_days(date_from, date_to, False), 15)

        date_from = datetime(2023, 4, 1)
        date_to = datetime(2023, 5, 5)
        self.assertEqual(self.calendar.get_base_days(date_from, date_to, False), 30)

    def test_get_calendar_for_country(self):
        calendar = self.env[
            "wizard.workalendar.holiday.import"
        ].get_calendar_for_country()
        self.assertTrue(calendar.exists())
        self.assertEqual(calendar.country_id.name, "Brazil")
