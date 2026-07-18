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

Recalibrated after dropping clear_caches() from move/aml unlink (systemic:
_sync_dynamic_lines unlinks term/tax lines mid-save, so the global cache was
being wiped inside the create/post flow itself):
    create_form: simple=732q  complex=7572q
    post:        simple=70q   complex=78q
    unlink:      87q

Limits are calibrated against the OCA CI environment (canonical reference:
the full localization is installed there, which legitimately costs more
queries than a minimal database — e.g. payment/EDI modules add triggers on
post). OCA CI, all patches applied (runs are deterministic across the
Odoo/OCB jobs, spread <=1q):
    create_form: simple=785q  complex=7995q
    post:        simple=104q  complex=169q
    unlink:      115q
Limits = CI measured * 1.15 rounded up; minimal-db runs stay far below.
Time is logged, never asserted.

edit_saved (saved-document edition) is a NEW step with no CI reference yet, so
its limits are calibrated LOCALLY (perf-oca warm=1 * 1.15) and must be
re-calibrated against the CI environment when this test first runs there, the
same way create_form/post were (CI installs the full localization -> higher
counts). It bumps the quantity of every line of an already-saved draft, which
propagates modified() to the ~60 document monetary totals -- the path narrowed
by the fiscal_amount_total_signal trigger. Measured warm=1 (perf-oca):
    edit_saved:  simple=127q  complex=687q
That count is IDENTICAL with and without the trigger (the change is
query-neutral; its gain is fewer modified() propagations / CPU, which the
query guard does not measure -- wall time is logged for reference only).
"""

from odoo.tests.common import tagged, warmup

from .common import AccountMoveBRCommon
from .perf_common import PerfMixin

LINES_SIMPLE = 2
LINES_COMPLEX = 30

QUERY_LIMIT_CREATE_SIMPLE = 905
QUERY_LIMIT_CREATE_COMPLEX = 9200
QUERY_LIMIT_POST_SIMPLE = 120
QUERY_LIMIT_POST_COMPLEX = 195
QUERY_LIMIT_UNLINK = 135

# edit_saved is a NEW step with no OCA CI reference yet: the limits below are
# LOCAL calibration (measured warm=1 on perf-oca * 1.15, rounded up) and will
# be re-calibrated against the CI environment once this test lands there, the
# same way the create_form/post limits were (see the header calibration note).
# Measured warm=1 (perf-oca): simple=127q, complex=687q (deterministic, and
# identical with/without the fiscal_amount_total_signal trigger -- that change
# is query-neutral; its gain is fewer modified() propagations, i.e. CPU).
QUERY_LIMIT_EDIT_SAVED_SIMPLE = 147
QUERY_LIMIT_EDIT_SAVED_COMPLEX = 791

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

    def _run_edit_saved(self, scenario, line_count):
        """Measure a representative edition of an already-SAVED draft invoice.

        Bumps the quantity of every product line of a saved draft. Each write
        re-flags the stored line amount fields; on flush they recompute and
        propagate ``modified()`` to the ~60 document monetary totals -- the
        cross-record (reverse o2m) path narrowed by the
        ``fiscal_amount_total_signal`` trigger. This is the CPU-bound
        saved-document edition scenario that the create_form/post steps do not
        exercise (there the lines are created, not re-written after save).
        """
        move = self.init_invoice(
            "out_invoice",
            products=self._line_products(line_count),
            document_type=self.document_type_55,
            document_serie_id=self.empresa_lc_document_55_serie_1,
            fiscal_operation=self.fo_venda,
            fiscal_operation_lines=[self.fo_venda_venda] * line_count,
        )
        self.assertEqual(move.state, "draft")
        with self._measure(scenario, "edit_saved", line_count):
            for line in move.invoice_line_ids:
                line.quantity += 1

    @warmup
    def test_invoice_performance(self):
        self._run_invoice_flow("simple", LINES_SIMPLE)
        self._run_invoice_flow("complex", LINES_COMPLEX)

        self._run_edit_saved("simple", LINES_SIMPLE)
        self._run_edit_saved("complex", LINES_COMPLEX)

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
        self._assert_queries("simple", "edit_saved", QUERY_LIMIT_EDIT_SAVED_SIMPLE)
        self._assert_queries("complex", "edit_saved", QUERY_LIMIT_EDIT_SAVED_COMPLEX)
        self._assert_queries("simple", "unlink_draft", QUERY_LIMIT_UNLINK)
        self._assert_scaling("create_form", "simple", "complex", SCALING_MAX_FACTOR)
        self._assert_scaling("post", "simple", "complex", SCALING_MAX_FACTOR)
        self._assert_scaling("edit_saved", "simple", "complex", SCALING_MAX_FACTOR)
