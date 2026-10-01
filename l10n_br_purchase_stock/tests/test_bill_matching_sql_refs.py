# Copyright (C) 2026 - Madooit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


class TestBillMatchingSQLRefs(TransactionCase):
    """Cover the duck-typed SQL reference hooks of the module.

    These methods are normally only executed by ``stock_picking_bill_matching``,
    which lives in another repository, so this suite makes sure they are
    exercised in the l10n-brazil CI as well.
    """

    def test_stock_move_reference_sql(self):
        sql = self.env["stock.move"]._get_bill_matching_reference_sql(alias="sm")
        self.assertTrue(sql.startswith("NULLIF("))
        self.assertIn("sm.partner_order", sql)
        self.assertIn("sm.partner_order_line", sql)

    def test_account_move_line_reference_sql(self):
        sql = self.env["account.move.line"]._get_bill_matching_reference_sql(
            alias="aml"
        )
        self.assertTrue(sql.startswith("NULLIF("))
        self.assertIn("aml.partner_order", sql)
        self.assertIn("aml.partner_order_line", sql)
