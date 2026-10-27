# Copyright (C) 2026-Today - KMEE (<https://kmee.com.br>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.tests.common_report_filters import (
    FiscalReportFiltersCase,
)


class TestSearchFilters(FiscalReportFiltersCase, TransactionCase):
    def test_sale_search_filters(self):
        self.assertFiscalFilters(
            "sale.order",
            present=[
                "fiscal_out",
                "fiscal_with_icmsst",
                "fiscal_groupby_document_type_id",
            ],
            # sale orders have no electronic document situation
            absent=["fiscal_issuer_company", "fiscal_edoc_not_void"],
        )
        self.assertFiscalFilters(
            "sale.order.line",
            present=["fiscal_cfop_interstate", "fiscal_groupby_cfop_id"],
        )
