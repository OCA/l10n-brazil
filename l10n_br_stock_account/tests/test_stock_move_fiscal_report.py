# Copyright (C) 2026-Today - KMEE (<https://kmee.com.br>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import TransactionCase


class TestStockMoveFiscalReport(TransactionCase):
    def test_search_view_filters(self):
        view = self.env.ref("l10n_br_stock_account.stock_move_fiscal_report_search")
        arch = self.env["stock.move"].get_views([(view.id, "search")])["views"][
            "search"
        ]["arch"]
        names = set(etree.fromstring(arch).xpath("//filter/@name"))
        self.assertTrue({"fiscal_out", "fiscal_cfop_internal"} <= names)
        self.assertIn("fiscal_groupby_cfop_id", names)
        # stock moves have no partner state nor electronic document situation
        self.assertNotIn("fiscal_groupby_partner_state_id", names)
        # related fields not stored are filters, never group bys
        self.assertNotIn("fiscal_groupby_cfop_destination", names)
        self.assertNotIn("fiscal_edoc_not_void", names)

    def test_group_by_cfop(self):
        domain = [("fiscal_operation_id", "!=", False)]
        moves = self.env["stock.move"].search(domain)
        self.assertTrue(moves)
        groups = self.env["stock.move"].read_group(
            domain, ["icms_value:sum"], ["cfop_id"], lazy=False
        )
        self.assertAlmostEqual(
            sum(group["icms_value"] for group in groups),
            sum(moves.mapped("icms_value")),
            places=2,
        )
