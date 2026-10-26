# Copyright (C) 2026-Today - KMEE (<https://kmee.com.br>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import TransactionCase

from .common_report_filters import FiscalReportFiltersCase


class TestDocumentLineReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report = cls.env["l10n_br_fiscal.document.line.report"]
        cls.document = cls.env.ref("l10n_br_fiscal.demo_nfe_same_state")

    def test_report_matches_document_lines(self):
        lines = self.document.fiscal_line_ids
        self.assertTrue(any(lines.mapped("icms_value")))
        rows = self.report.search([("document_id", "=", self.document.id)])
        self.assertEqual(len(rows), len(lines))
        for fname in ("icms_base", "icms_value", "ipi_value", "pis_value"):
            self.assertAlmostEqual(
                sum(rows.mapped(fname)), sum(lines.mapped(fname)), places=2
            )
        # document total before the withholdings, as in the NF-e
        self.assertAlmostEqual(
            sum(rows.mapped("amount_total")),
            sum(lines.mapped("fiscal_amount_total"))
            + sum(lines.mapped("amount_tax_withholding")),
            places=2,
        )
        self.assertEqual(
            set(rows.mapped("fiscal_operation_type")),
            {self.document.fiscal_operation_type},
        )

    def test_group_by_cfop_and_rate(self):
        groups = self.report.read_group(
            [("document_id", "=", self.document.id)],
            ["icms_value:sum"],
            ["cfop_id", "icms_rate"],
            lazy=False,
        )
        self.assertAlmostEqual(
            sum(group["icms_value"] for group in groups),
            sum(self.document.fiscal_line_ids.mapped("icms_value")),
            places=2,
        )

    def test_search_view_filters(self):
        arch = self.report.get_views([(False, "search")])["views"]["search"]["arch"]
        doc = etree.fromstring(arch)
        self.assertFalse(doc.xpath("//separator[@name]"))
        names = set(doc.xpath("//filter/@name"))
        self.assertTrue(
            {"fiscal_out", "fiscal_edoc_not_void", "fiscal_groupby_cfop_id"} <= names
        )


class TestFiscalDocumentSearchFilters(FiscalReportFiltersCase, TransactionCase):
    def test_document_search_filters(self):
        filters = self.assertFiscalFilters(
            "l10n_br_fiscal.document",
            present=["fiscal_out", "fiscal_issuer_company", "fiscal_edoc_not_void"],
            # line fields are not in the document
            absent=["fiscal_cfop_internal", "fiscal_products"],
        )
        # the document uses its totals for the tax filters
        self.assertIn("amount_icmsst_value", filters["fiscal_with_icmsst"])
