# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Unit tests of the identifier of an event, with no database involved."""

from datetime import datetime
from unittest import TestCase

from odoo.addons.l10n_br_reinf.tools.reinf_id import (
    EVENT_ID_LENGTH,
    SEQUENCE_MAX,
    ReinfIdError,
    build_event_id,
    pad_inscription,
    validate_event_id,
)

MOMENT = datetime(2026, 8, 11, 22, 9, 5)
MOMENT_STAMP = "20260811220905"


class TestReinfId(TestCase):
    def test_build_from_cnpj_root(self):
        """The identifier is ID, tpInsc, nrInsc padded, the moment and the
        sequential."""
        event_id = build_event_id("1", "12.345.678", MOMENT, 7)
        self.assertEqual(
            event_id, "ID" + "1" + "12345678000000" + MOMENT_STAMP + "00007"
        )
        self.assertEqual(len(event_id), EVENT_ID_LENGTH)

    def test_build_from_cpf(self):
        """A CPF has 11 positions and is padded with 3 zeros."""
        event_id = build_event_id("2", "123.456.789-09", MOMENT, 1)
        self.assertEqual(
            event_id, "ID" + "2" + "12345678909000" + MOMENT_STAMP + "00001"
        )

    def test_build_from_alphanumeric_cnpj(self):
        """The alphanumeric CNPJ of the NT 03/2026 fits the pattern."""
        event_id = build_event_id("1", "A8.7HB.ZHB/0001-61", MOMENT, 0)
        self.assertEqual(
            event_id, "ID" + "1" + "A87HBZHB000161" + MOMENT_STAMP + "00000"
        )
        self.assertTrue(validate_event_id(event_id))

    def test_sequence_wraps(self):
        """The sequential has 5 positions, so it wraps instead of overflowing."""
        event_id = build_event_id("1", "12345678", MOMENT, SEQUENCE_MAX + 3)
        self.assertTrue(event_id.endswith("00002"))
        self.assertEqual(len(event_id), EVENT_ID_LENGTH)

    def test_pad_inscription(self):
        self.assertEqual(pad_inscription("12.345.678"), "12345678000000")
        self.assertEqual(pad_inscription("a87hbzhb000161"), "A87HBZHB000161")

    def test_pad_inscription_refuses_empty(self):
        with self.assertRaises(ReinfIdError):
            pad_inscription("  ")

    def test_pad_inscription_refuses_too_long(self):
        with self.assertRaises(ReinfIdError):
            pad_inscription("123456789012345")

    def test_build_refuses_unknown_inscription_type(self):
        with self.assertRaises(ReinfIdError):
            build_event_id("3", "12345678", MOMENT, 1)

    def test_validate_refuses_wrong_length(self):
        with self.assertRaises(ReinfIdError):
            validate_event_id("ID" + "1" + "12345678000000" + MOMENT_STAMP)

    def test_validate_refuses_letter_in_the_check_digits(self):
        """Only the 12 first positions of the inscription accept letters."""
        with self.assertRaises(ReinfIdError):
            validate_event_id("ID" + "1" + "1234567800000A" + MOMENT_STAMP + "00001")
