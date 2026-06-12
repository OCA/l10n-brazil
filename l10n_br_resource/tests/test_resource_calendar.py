# Copyright 2016 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.tests.common as test_common
from odoo import fields
from odoo.exceptions import UserError


class TestResourceCalendar(test_common.SingleTransactionCase):
    def setUp(self):
        super().setUp()

        self.resource_calendar = self.env["resource.calendar"]
        self.resource_leaves = self.env["resource.calendar.leaves"]
        self.holiday_import = self.env["wizard.workalendar.holiday.import"]

        self.nacional_calendar_id = self.resource_calendar.create(
            {
                "name": "Calendario Nacional",
                "country_id": self.env.ref("base.br").id,
            }
        )

        self.resource_1 = self.env["resource.resource"].create(
            {
                "name": "Teste Resource 1",
                "resource_type": "user",
                "calendar_id": self.nacional_calendar_id.id,
            }
        )
        self.resource_2 = self.env["resource.resource"].create(
            {
                "name": "Teste Resource 2",
                "resource_type": "user",
                "calendar_id": self.nacional_calendar_id.id,
            }
        )

        self.leave_nacional_01 = self.resource_leaves.create(
            {
                "name": "Tiradentes",
                "date_from": fields.Datetime.to_datetime("2016-03-21 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2016-03-21 23:59:59"),
                "calendar_id": self.nacional_calendar_id.id,
                "leave_type": "F",
                "coverage": "N",
                "resource_id": self.resource_1.id,
            }
        )
        self.estadual_calendar_id = self.resource_calendar.create(
            {
                "name": "Calendario Estadual",
                "parent_id": self.nacional_calendar_id.id,
            }
        )
        self.leave_estadual_01 = self.resource_leaves.create(
            {
                "name": "Aniversario de SP",
                "date_from": fields.Datetime.to_datetime("2016-01-25 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2016-01-25 23:59:59"),
                "calendar_id": self.estadual_calendar_id.id,
                "leave_type": "F",
                "coverage": "E",
            }
        )
        self.municipal_calendar_id = self.resource_calendar.create(
            {
                "name": "Calendario Municipal",
                "parent_id": self.estadual_calendar_id.id,
            }
        )
        self.leave_municipal_01 = self.resource_leaves.create(
            {
                "name": "Aniversario Chapeco",
                "date_from": fields.Datetime.to_datetime("2016-08-25 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2016-08-25 23:59:59"),
                "calendar_id": self.municipal_calendar_id.id,
                "leave_type": "F",
                "coverage": "M",
            }
        )

        # Test workalendar_holiday_import

        self.calendar_id_sp = self.resource_calendar.create(
            {
                "name": "Calendario de Sao Paulo",
                "country_id": self.env.ref("base.br").id,
                "state_id": self.env.ref("base.state_br_sp").id,
                "l10n_br_city_id": self.env.ref("l10n_br_base.city_3500105").id,
            }
        )

    def test_00_add_leave_nacional(self):
        """Add a new holiday to the national calendar"""
        self.leave_nacional_02 = self.resource_leaves.create(
            {
                "name": "Natal",
                "date_from": fields.Datetime.to_datetime("2016-12-24 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2016-12-24 23:59:59"),
                "calendar_id": self.nacional_calendar_id.id,
                "leave_type": "F",
                "coverage": "N",
            }
        )
        self.assertEqual(self.leave_nacional_02.name, "Natal")
        self.assertEqual(self.leave_nacional_02.calendar_id, self.nacional_calendar_id)
        self.assertEqual(2, len(self.nacional_calendar_id.leave_ids))

    def test_01_add_leave_estadual(self):
        """Add a new holiday to the state calendar"""
        self.leave_estadual_02 = self.resource_leaves.create(
            {
                "name": "Aniversario MG",
                "date_from": fields.Datetime.to_datetime("2016-07-16 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2016-07-16 23:59:59"),
                "calendar_id": self.estadual_calendar_id.id,
                "leave_type": "F",
                "coverage": "E",
            }
        )
        self.assertEqual(self.leave_estadual_02.name, "Aniversario MG")
        self.assertEqual(self.leave_estadual_02.calendar_id, self.estadual_calendar_id)
        self.assertEqual(3, len(self.estadual_calendar_id.leave_ids))

    def test_02_add_leave_municipal(self):
        """Add a new holiday to the municipal calendar"""
        self.leave_municipal_02 = self.resource_leaves.create(
            {
                "name": "Aniversario Itajuba",
                "date_from": fields.Datetime.to_datetime("2016-03-19 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2016-03-19 23:59:59"),
                "calendar_id": self.municipal_calendar_id.id,
                "leave_type": "F",
                "coverage": "M",
            }
        )
        self.assertEqual(self.leave_municipal_02.name, "Aniversario Itajuba")
        self.assertEqual(
            self.leave_municipal_02.calendar_id, self.municipal_calendar_id
        )
        self.assertEqual(4, len(self.municipal_calendar_id.leave_ids))

    def test_03_is_holiday(self):
        date = fields.Datetime.to_datetime("2016-08-25 00:00:01")
        self.assertTrue(self.municipal_calendar_id.is_holiday(date))

    def test_04_get_leave_intervals(self):
        self.holidays = self.municipal_calendar_id.get_leave_intervals(
            start_datetime=fields.Datetime.to_datetime("2016-08-01 00:00:00"),
            end_datetime=fields.Datetime.to_datetime("2016-08-31 00:00:00"),
        )
        self.assertEqual(1, len(self.holidays))

        self.estadual_calendar_id.get_leave_intervals(
            start_datetime=fields.Datetime.to_datetime("2016-01-01 00:00:00"),
            end_datetime=fields.Datetime.to_datetime("2016-01-20 00:00:00"),
        )
        self.nacional_calendar_id.get_leave_intervals(
            resource_id=self.resource_1.id,
            start_datetime=fields.Datetime.to_datetime("2016-03-01 00:00:00"),
            end_datetime=fields.Datetime.to_datetime("2016-03-31 00:00:00"),
        )
        self.nacional_calendar_id.get_leave_intervals(
            resource_id=self.resource_2.id,
            start_datetime=fields.Datetime.to_datetime("2016-03-01 00:00:00"),
            end_datetime=fields.Datetime.to_datetime("2016-03-31 00:00:00"),
        )

    def test_05_is_extended_holiday(self):
        date = fields.Datetime.to_datetime("2016-08-25 00:00:01")
        self.assertTrue(self.municipal_calendar_id.is_extended_holiday(date))
        date = fields.Datetime.to_datetime("2016-03-19 00:00:01")
        self.assertFalse(self.municipal_calendar_id.is_extended_holiday(date))

    def test_06_next_business_day(self):
        """Given a date, get the next business day"""
        # 21-03 is a holiday
        day_before_holiday = fields.Datetime.to_datetime("2016-03-20 00:00:01")
        next_day = self.municipal_calendar_id.next_business_day(day_before_holiday)
        self.assertEqual(
            next_day,
            fields.Datetime.to_datetime("2016-03-22 00:00:01"),
            "Starting from a holiday, next business day is invalid",
        )

        day_before_weekend = fields.Datetime.to_datetime("2016-12-16 00:00:01")
        next_day = self.municipal_calendar_id.next_business_day(day_before_weekend)
        self.assertEqual(
            next_day,
            fields.Datetime.to_datetime("2016-12-19 00:00:01"),
            "Starting from a weekend, next business day is invalid",
        )
        # No date
        self.municipal_calendar_id.next_business_day(False)

    def test_07_get_base_days(self):
        """Given a time interval, return the number of base days
        for payroll calculations"""
        start_date = fields.Datetime.to_datetime("2017-01-01 00:00:01")
        end_date = fields.Datetime.to_datetime("2017-01-31 23:59:59")

        total = self.resource_calendar.get_base_days(start_date, end_date)
        self.assertEqual(total, 30, "Base days calculation for January is incorrect")

        start_date = fields.Datetime.to_datetime("2017-02-01 00:00:01")
        end_date = fields.Datetime.to_datetime("2017-02-28 23:59:59")

        total = self.resource_calendar.get_base_days(start_date, end_date)
        self.assertEqual(total, 30, "Base days calculation for February is incorrect")
        # No date
        self.resource_calendar.get_base_days(False, False)

    def test_08_is_business_day(self):
        """Check if dates are business days"""
        monday = fields.Datetime.to_datetime("2017-01-09 00:00:01")
        tuesday = fields.Datetime.to_datetime("2017-01-10 00:00:01")
        saturday = fields.Datetime.to_datetime("2017-01-07 00:00:01")
        sunday = fields.Datetime.to_datetime("2017-01-08 00:00:01")
        holiday = fields.Datetime.to_datetime("2016-08-25 00:00:00")

        self.assertTrue(
            self.municipal_calendar_id.is_business_day(monday),
            "ERROR: Monday is a business day!",
        )
        self.assertTrue(
            self.municipal_calendar_id.is_business_day(tuesday),
            "ERROR: Tuesday is a business day!",
        )

        self.assertTrue(
            not self.municipal_calendar_id.is_business_day(saturday),
            "ERROR: Saturday is not a business day!",
        )
        self.assertTrue(
            not self.municipal_calendar_id.is_business_day(sunday),
            "ERROR: Sunday is not a business day!",
        )

        self.assertTrue(
            not self.municipal_calendar_id.is_business_day(holiday),
            "ERROR: Holiday is not a business day!",
        )

        self.leave_nacional_02 = self.resource_leaves.create(
            {
                "name": "Feriado 2017",
                "date_from": fields.Datetime.to_datetime("2017-01-21 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2017-01-21 23:59:59"),
                "calendar_id": self.nacional_calendar_id.id,
                "leave_type": "F",
                "coverage": "N",
            }
        )
        holiday2 = fields.Datetime.to_datetime("2017-01-21 00:00:00")
        self.assertTrue(
            not self.municipal_calendar_id.is_business_day(holiday2),
            "ERROR: Holiday2 is not a business day!",
        )
        # No date
        self.municipal_calendar_id.is_business_day(False)

    def test_09_count_business_days(self):
        """Count the number of business days."""
        start_date = fields.Datetime.to_datetime("2017-01-01 00:00:01")
        end_date = fields.Datetime.to_datetime("2017-01-31 23:59:59")

        total_business_days = self.resource_calendar.count_business_days(
            start_date, end_date
        )
        self.assertEqual(
            total_business_days,
            22,
            "ERROR: Total business days for Jan/2017 is invalid",
        )

        start_date = fields.Datetime.to_datetime("2018-01-01 00:00:01")
        end_date = fields.Datetime.to_datetime("2018-01-31 23:59:59")

        total_business_days = self.resource_calendar.count_business_days(
            start_date, end_date
        )
        self.assertEqual(
            total_business_days,
            23,
            "ERROR: Total business days for Jan/2018 is invalid",
        )
        # No date
        self.resource_calendar.count_business_days(False, False)

    def test_10_is_bank_holiday(self):
        """Validate if date is a bank holiday."""
        # adding bank holiday
        self.resource_leaves.create(
            {
                "name": "Feriado Bancario",
                "date_from": fields.Datetime.to_datetime("2017-01-13 00:00:00"),
                "date_to": fields.Datetime.to_datetime("2017-01-13 23:59:59"),
                "calendar_id": self.nacional_calendar_id.id,
                "leave_type": "B",
                "coverage": "N",
            }
        )
        date = fields.Datetime.to_datetime("2017-01-13 01:02:03")
        self.assertTrue(self.nacional_calendar_id.is_bank_holiday(date))

    def test_12_get_country_from_calendar(self):
        """Validate that the country returned for the holiday is correct."""
        holiday = self.holiday_import.create(
            {
                "interval_type": "days",
                "calendar_id": self.nacional_calendar_id.id,
            }
        )

        country_id = self.holiday_import.get_country_from_calendar(holiday)
        self.assertEqual(country_id.code, "BR", "Incorrect country.")

    def test_16_next_bank_business_day(self):
        date = fields.Datetime.to_datetime("2017-01-13 00:00:00")
        next_day = self.nacional_calendar_id.next_bank_business_day(date)
        self.assertEqual(next_day, fields.Datetime.to_datetime("2017-01-16 00:00:00"))
        # No date
        self.nacional_calendar_id.next_bank_business_day(False)

    def test_17_holiday_import(self):
        holiday = self.holiday_import.create(
            {
                "start_date": fields.Datetime.to_datetime("2018-08-28 00:00:00"),
                "interval_type": "years",
                "calendar_id": self.nacional_calendar_id.id,
            }
        )
        res = holiday.holiday_import()
        self.assertTrue(res)
        date = fields.Datetime.to_datetime("2019-03-05 00:00:00")
        self.assertTrue(self.nacional_calendar_id.is_bank_holiday(date))

    def test_18_is_bank_business_day(self):
        date = fields.Datetime.to_datetime("2017-01-16 00:00:00")
        self.assertTrue(self.nacional_calendar_id.is_bank_business_day(date))
        date = fields.Datetime.to_datetime("2017-01-13 00:00:00")
        self.assertFalse(self.nacional_calendar_id.is_bank_business_day(date))
        # No date
        self.nacional_calendar_id.is_bank_business_day(False)

    def test_19_check_constraint_recursive(self):
        """Test resource.calendar constrains methods"""
        with self.assertRaises(UserError):
            self.nacional_calendar_id.write(
                {"parent_id": self.municipal_calendar_id.id}
            )
