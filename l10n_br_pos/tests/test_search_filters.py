# Copyright (C) 2026-Today - KMEE (<https://kmee.com.br>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.tests.common_report_filters import (
    FiscalReportFiltersCase,
)


class TestSearchFilters(FiscalReportFiltersCase, TransactionCase):
    def test_pos_order_search_filters(self):
        self.assertFiscalFilters(
            "pos.order",
            present=["fiscal_out", "fiscal_groupby_fiscal_operation_id"],
            absent=["fiscal_cfop_internal"],
        )
