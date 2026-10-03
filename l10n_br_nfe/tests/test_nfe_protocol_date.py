# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from xsdata.models.datatype import XmlDateTime

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_nfe.tools import tax_authority_date_to_utc


class TestNFeProtocolDate(TransactionCase):
    def test_brasilia_offset_to_utc(self):
        self.assertEqual(
            tax_authority_date_to_utc("2026-10-02T10:15:00-03:00"),
            "2026-10-02 13:15:00",
        )

    def test_other_offset_to_utc(self):
        # MT and AM are at -04:00, AC at -05:00.
        self.assertEqual(
            tax_authority_date_to_utc("2026-10-02T10:15:00-04:00"),
            "2026-10-02 14:15:00",
        )
        self.assertEqual(
            tax_authority_date_to_utc("2026-10-02T10:15:00-05:00"),
            "2026-10-02 15:15:00",
        )

    def test_crosses_midnight(self):
        self.assertEqual(
            tax_authority_date_to_utc("2026-10-02T22:30:00-03:00"),
            "2026-10-03 01:30:00",
        )

    def test_xsdata_and_datetime_inputs(self):
        self.assertEqual(
            tax_authority_date_to_utc(
                XmlDateTime.from_string("2026-10-02T10:15:00-03:00")
            ),
            "2026-10-02 13:15:00",
        )
        self.assertEqual(
            tax_authority_date_to_utc(
                datetime.fromisoformat("2026-10-02T10:15:00-03:00")
            ),
            "2026-10-02 13:15:00",
        )

    def test_naive_and_empty(self):
        self.assertEqual(
            tax_authority_date_to_utc(datetime(2026, 10, 2, 10, 15)),
            "2026-10-02 10:15:00",
        )
        self.assertFalse(tax_authority_date_to_utc(False))
