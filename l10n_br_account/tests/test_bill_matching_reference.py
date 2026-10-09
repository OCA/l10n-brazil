# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import TransactionCase


class TestBillMatchingReferenceSQL(TransactionCase):
    """The account.move.line side of the stock_picking_bill_matching
    duck-typing hook: normalization rules, exercised against literal rows so
    no document setup is needed."""

    def _eval_ref(self, partner_order, partner_order_line):
        expr = self.env["account.move.line"]._get_bill_matching_reference_sql("aml")
        self.env.cr.execute(
            f"""
            SELECT ({expr}) FROM (
                SELECT %s::varchar AS partner_order, %s::varchar AS partner_order_line
            ) aml
            """,
            (partner_order, partner_order_line),
        )
        return self.env.cr.fetchone()[0]

    def test_null_when_no_reference(self):
        self.assertIsNone(self._eval_ref(None, None))
        self.assertIsNone(self._eval_ref("", ""))
        self.assertIsNone(self._eval_ref("  ", "  "))

    def test_reference_plain(self):
        self.assertEqual(self._eval_ref("P00015", "1"), "P00015-1")

    def test_item_numeric_normalization(self):
        # Cristiano's case: P00015-1 must reconcile with P00015-001
        self.assertEqual(self._eval_ref("P00015", "001"), "P00015-1")
        self.assertEqual(self._eval_ref("P00015", " 001 "), "P00015-1")

    def test_item_non_numeric_kept(self):
        self.assertEqual(self._eval_ref("P00015", "ABC"), "P00015-ABC")

    def test_truncation_matches_field_sizes(self):
        # partner_order is a Char(15), partner_order_line a Char(6)
        self.assertEqual(
            self._eval_ref("A-VERY-LONG-ORDER-NAME", "1234567"),
            "A-VERY-LONG-ORD-123456",
        )
