# Copyright (C) 2026-Today - KMEE (<https://kmee.com.br>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.tests.common_report_filters import (
    FiscalReportFiltersCase,
)


class TestSearchFilters(FiscalReportFiltersCase, TransactionCase):
    def test_purchase_search_filters(self):
        for xmlid in (
            "purchase.view_purchase_order_filter",
            "purchase.purchase_order_view_search",
        ):
            self.assertFiscalFilters(
                "purchase.order",
                present=["fiscal_in", "fiscal_with_ipi"],
                absent=["fiscal_edoc_not_void"],
                view_id=self.env.ref(xmlid).id,
            )
        self.assertFiscalFilters(
            "purchase.order.line",
            present=["fiscal_cfop_interstate", "fiscal_groupby_ncm_id"],
        )
