# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Performance baseline + regression guard for the BR invoice flow (Form path).

Covers the UI-like path: invoice created through ``Form`` (all onchanges run
per line, like a user typing) and then posted, with a small and a large line
count. A separate draft-invoice unlink is measured last (it clears registry
caches, see l10n_br_account/models/account_move.py).

Baseline (calibration):
    date=2026-07-17 sha=683173c078 (OCA 16.0) db=perf-oca
    (clean: l10n_br_account,l10n_br_sale,l10n_br_coa_generic,l10n_br_coa_simple + demo)
    create_form: simple=975q (1.79s)  complex=7709q (21.2s)
    post:        simple=122q (0.07s)  complex=130q (0.19s)
    unlink:      115q (0.12s)
Limits = measured * 1.15 rounded up. Time is logged, never asserted.
"""

from odoo.tests.common import tagged, warmup

from .common import AccountMoveBRCommon
from .perf_common import PerfMixin

LINES_SIMPLE = 2
LINES_COMPLEX = 30

QUERY_LIMIT_CREATE_SIMPLE = 1150
QUERY_LIMIT_CREATE_COMPLEX = 8900
QUERY_LIMIT_POST_SIMPLE = 150
QUERY_LIMIT_POST_COMPLEX = 160
QUERY_LIMIT_UNLINK = 140

# queries/line(complex) <= factor * queries/line(simple): catches O(n^2).
SCALING_MAX_FACTOR = 1.5


@tagged("post_install", "-at_install", "l10n_br_performance")
class TestL10nBrAccountPerformance(PerfMixin, AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()
        cls.document_type_55 = cls.env.ref("l10n_br_fiscal.document_55")
        cls.fo_venda = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fo_venda_venda = cls.env.ref("l10n_br_fiscal.fo_venda_venda")

    def _line_products(self, count):
        # Cyclic A/B mix: two distinct fiscal mappings, repeated lines —
        # realistic (production repeats products) while keeping more than one
        # mapping key so a future mapping cache cannot trivialize the test.
        pool = [self.product_a, self.product_b]
        return [pool[index % 2] for index in range(count)]

    def _run_invoice_flow(self, scenario, line_count):
        products = self._line_products(line_count)
        with self._measure(scenario, "create_form", line_count):
            move = self.init_invoice(
                "out_invoice",
                products=products,
                document_type=self.document_type_55,
                document_serie_id=self.empresa_lc_document_55_serie_1,
                fiscal_operation=self.fo_venda,
                fiscal_operation_lines=[self.fo_venda_venda] * line_count,
            )
        with self._measure(scenario, "post", line_count):
            move.action_post()
        return move

    @warmup
    def test_invoice_performance(self):
        self._run_invoice_flow("simple", LINES_SIMPLE)
        self._run_invoice_flow("complex", LINES_COMPLEX)

        # Measured last on purpose: account.move unlink currently clears the
        # registry caches, which would make any step measured after it run
        # cold again.
        draft_move = self.init_invoice(
            "out_invoice",
            products=self._line_products(LINES_SIMPLE),
            document_type=self.document_type_55,
            document_serie_id=self.empresa_lc_document_55_serie_1,
            fiscal_operation=self.fo_venda,
            fiscal_operation_lines=[self.fo_venda_venda] * LINES_SIMPLE,
        )
        with self._measure("simple", "unlink_draft", LINES_SIMPLE):
            draft_move.unlink()

        self._assert_queries("simple", "create_form", QUERY_LIMIT_CREATE_SIMPLE)
        self._assert_queries("complex", "create_form", QUERY_LIMIT_CREATE_COMPLEX)
        self._assert_queries("simple", "post", QUERY_LIMIT_POST_SIMPLE)
        self._assert_queries("complex", "post", QUERY_LIMIT_POST_COMPLEX)
        self._assert_queries("simple", "unlink_draft", QUERY_LIMIT_UNLINK)
        self._assert_scaling("create_form", "simple", "complex", SCALING_MAX_FACTOR)
        self._assert_scaling("post", "simple", "complex", SCALING_MAX_FACTOR)
