from datetime import date, datetime

from odoo.tests import common


class TestResourceCalendar(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.calendar = self.env["resource.calendar"].create({"name": "Test Calendar"})

        self.env["resource.calendar.leaves"].create(
            {
                "name": "Christmas",
                "date_from": date(2023, 12, 25),
                "date_to": date(2023, 12, 25),
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
        reference_date = datetime.now()
        leaves_count = self.env["resource.calendar.leaves"].search_count(
            [
                ("date_from", "<=", reference_date),
                ("date_to", ">=", reference_date),
                ("leave_type", "in", ["F", "B"]),
            ]
        )
        self.assertEqual(leaves_count, self.calendar.is_bank_holiday(reference_date))

        reference_date = datetime(2023, 4, 21)
        leaves_count = self.env["resource.calendar.leaves"].search_count(
            [
                ("date_from", "<=", reference_date),
                ("date_to", ">=", reference_date),
                ("leave_type", "in", ["F", "B"]),
            ]
        )
        self.assertEqual(leaves_count, self.calendar.is_bank_holiday(reference_date))

        reference_date = datetime(2023, 4, 13)
        leaves_count = self.env["resource.calendar.leaves"].search_count(
            [
                ("date_from", "<=", reference_date),
                ("date_to", ">=", reference_date),
                ("leave_type", "in", ["F", "B"]),
            ]
        )
        self.assertEqual(leaves_count, self.calendar.is_bank_holiday(reference_date))
        # No date
        self.calendar.is_bank_holiday(False)

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
