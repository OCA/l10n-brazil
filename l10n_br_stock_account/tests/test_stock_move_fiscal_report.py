# Copyright (C) 2026-Today - KMEE (<https://kmee.com.br>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from .common import TestBrPickingInvoicingCommon


class TestStockMoveFiscalReport(TestBrPickingInvoicingCommon):
    # The moves with a fiscal operation come from the pickings of the test
    # base: the OCA CI of 19.0 installs no demo data.

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
        # read_group is deprecated since 19.0
        groups = self.env["stock.move"]._read_group(
            domain, ["cfop_id"], ["icms_value:sum"]
        )
        self.assertAlmostEqual(
            sum(icms_value for _cfop, icms_value in groups),
            sum(moves.mapped("icms_value")),
            places=2,
        )

    def test_get_view_cache_follows_company_country(self):
        """A foreign company must not get the cached Brazilian form view."""
        foreign = self.env["res.company"].create(
            {"name": "Foreign company", "country_id": self.env.ref("base.us").id}
        )
        brazilian = self.env["res.company"].create(
            {"name": "Brazilian company", "country_id": self.env.ref("base.br").id}
        )
        self.env.registry.clear_cache("templates")
        archs = [
            self.env["stock.picking"]
            .with_company(company)
            .get_view(view_type="form")["arch"]
            for company in (brazilian, foreign)
        ]
        self.assertIn('name="icms_cst_id"', archs[0])
        self.assertNotIn('name="icms_cst_id"', archs[1])
