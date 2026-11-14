# Copyright (C) 2026-Today - KMEE (<https://kmee.com.br>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.tests.common_report_filters import (
    FiscalReportFiltersCase,
)


class TestSearchFilters(FiscalReportFiltersCase, TransactionCase):
    def test_invoice_search_filters(self):
        self.assertFiscalFilters(
            "account.move",
            present=["fiscal_with_icmsst", "fiscal_edoc_not_void"],
            # fiscal_operation_type is a non searchable compute on account.move:
            # the core move_type filters already split incoming and outgoing
            absent=["fiscal_out", "fiscal_cfop_internal"],
        )
        self.assertFiscalFilters(
            "account.move.line",
            present=["fiscal_out", "fiscal_cfop_interstate", "fiscal_with_icmsst"],
        )
