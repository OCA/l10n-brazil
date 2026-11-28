# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from datetime import datetime, timedelta, timezone

from xsdata.models.datatype import XmlDate, XmlDateTime

from odoo.tests import TransactionCase

from ..models.spec_import import datetime_to_utc


class TestSpecImportDatetime(TransactionCase):
    """The Odoo Datetime fields keep naive UTC, the XML carries local time
    with an offset: the import must convert instead of dropping the offset."""

    def test_negative_offset(self):
        self.assertEqual(
            datetime_to_utc("2026-11-01T01:00:00-03:00"),
            datetime(2026, 11, 1, 4, 0, 0),
        )

    def test_negative_offset_changes_the_day(self):
        self.assertEqual(
            datetime_to_utc("2026-10-31T22:30:00-03:00"),
            datetime(2026, 11, 1, 1, 30, 0),
        )

    def test_offset_with_two_digit_hours(self):
        self.assertEqual(
            datetime_to_utc("2026-11-01T10:00:00-10:00"),
            datetime(2026, 11, 1, 20, 0, 0),
        )

    def test_positive_offset(self):
        self.assertEqual(
            datetime_to_utc("2026-11-01T01:00:00+02:00"),
            datetime(2026, 10, 31, 23, 0, 0),
        )

    def test_zero_offset_and_z(self):
        expected = datetime(2026, 11, 1, 1, 0, 0)
        self.assertEqual(datetime_to_utc("2026-11-01T01:00:00+00:00"), expected)
        self.assertEqual(datetime_to_utc("2026-11-01T01:00:00Z"), expected)

    def test_offset_without_colon_and_with_minutes(self):
        self.assertEqual(
            datetime_to_utc("2026-11-01T01:00:00-0330"),
            datetime(2026, 11, 1, 4, 30, 0),
        )

    def test_without_offset_is_kept(self):
        self.assertEqual(
            datetime_to_utc("2026-11-01T01:00:00"), datetime(2026, 11, 1, 1, 0, 0)
        )

    def test_fraction_of_second(self):
        self.assertEqual(
            datetime_to_utc("2026-11-01T01:00:00.123-03:00"),
            datetime(2026, 11, 1, 4, 0, 0),
        )
        self.assertEqual(
            datetime_to_utc("2026-11-01T01:00:00.123456"),
            datetime(2026, 11, 1, 1, 0, 0),
        )

    def test_value_without_time_is_kept(self):
        self.assertEqual(datetime_to_utc("2026-11-01"), "2026-11-01")

    def test_xsdata_date_is_midnight(self):
        self.assertEqual(
            datetime_to_utc(XmlDate(2026, 11, 1)), datetime(2026, 11, 1, 0, 0, 0)
        )

    def test_xsdata_datetime(self):
        self.assertEqual(
            datetime_to_utc(XmlDateTime(2026, 11, 1, 1, 0, 0, offset=-180)),
            datetime(2026, 11, 1, 4, 0, 0),
        )
        self.assertEqual(
            datetime_to_utc(XmlDateTime(2026, 11, 1, 1, 0, 0)),
            datetime(2026, 11, 1, 1, 0, 0),
        )

    def test_python_datetime(self):
        aware = datetime(2026, 11, 1, 1, 0, 0, tzinfo=timezone(timedelta(hours=-3)))
        self.assertEqual(datetime_to_utc(aware), datetime(2026, 11, 1, 4, 0, 0))
        self.assertEqual(
            datetime_to_utc(datetime(2026, 11, 1, 1, 0, 0)),
            datetime(2026, 11, 1, 1, 0, 0),
        )

    def test_invalid_value_raises(self):
        with self.assertRaises(ValueError):
            datetime_to_utc("2026-11-01Tgarbage")
