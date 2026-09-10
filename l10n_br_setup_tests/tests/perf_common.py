# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Performance measurement helpers for l10n_br test suites.

Design notes
------------
* Every measured step logs a stable, greppable line::

    PERF l10n_br | warm=1 scenario=complex lines=30 step=post time=3.421s ...

  ``grep "PERF l10n_br" odoo.log | grep warm=1`` gives the numbers that
  matter (the cold round measures registry/cache warmup on top of the code).

* Regression guards are based on **query counts** (deterministic) and on the
  **queries-per-line scaling ratio** between a small and a large scenario
  (catches O(n^2) behavior on any machine speed). Wall time is always
  measured and logged but never asserted: absolute time limits are flaky on
  shared CI runners.

* Set ``L10N_BR_PERF_STRICT=0`` to switch the guards off (log-only mode) when
  running on databases with extra modules installed (module inheritance adds
  queries and skews absolute counts). The scaling-ratio guard is immune to a
  constant per-line offset, but is disabled together for simplicity.

* Recalibration: when a legitimate change moves the numbers, run with
  ``L10N_BR_PERF_STRICT=0``, take the ``warm=1`` numbers from the log and set
  the limit constants to ``measured * 1.15`` (rounded up), documenting the
  raw numbers in the test file header.
"""

import logging
import os
import time
from contextlib import contextmanager

_logger = logging.getLogger(__name__)

PERF_STRICT = os.environ.get("L10N_BR_PERF_STRICT", "1") == "1"


class PerfMixin:
    """Mixin for TransactionCase tests measuring time and query counts."""

    @property
    def _perf_results(self):
        if not hasattr(self, "_perf_results_store"):
            self._perf_results_store = {}
        return self._perf_results_store

    @contextmanager
    def _measure(self, scenario, step, lines):
        """Measure wall time and SQL query count of the enclosed block.

        Flushes before entering (so pending computations from previous steps
        are not accounted here) and before leaving (so the flush caused by
        the measured step is accounted here) — same semantics as the core
        ``assertQueryCount``.
        """
        self.env.flush_all()
        queries_before = self.env.cr.sql_log_count
        time_before = time.perf_counter()
        yield
        self.env.flush_all()
        elapsed = time.perf_counter() - time_before
        queries = self.env.cr.sql_log_count - queries_before
        warm = getattr(self, "warm", True)
        if warm:
            self._perf_results[(scenario, step)] = {
                "time": elapsed,
                "queries": queries,
                "lines": lines,
            }
        _logger.info(
            "PERF l10n_br | warm=%d scenario=%s lines=%d step=%s "
            "time=%.3fs queries=%d q_per_line=%.1f",
            warm,
            scenario,
            lines,
            step,
            elapsed,
            queries,
            queries / lines if lines else queries,
        )

    def _assert_queries(self, scenario, step, limit):
        """Guard: absolute query count of a step (warm round only)."""
        if not PERF_STRICT or not getattr(self, "warm", True):
            return
        result = self._perf_results[(scenario, step)]
        self.assertLessEqual(
            result["queries"],
            limit,
            "Query count regression in %s/%s: %d > %d. If your change "
            "legitimately needs more queries, recalibrate the limit constant "
            "(see perf_common.py docstring)."
            % (scenario, step, result["queries"], limit),
        )

    def _assert_scaling(self, step, simple_scenario, complex_scenario, max_factor):
        """Guard: queries-per-line must not blow up with the line count.

        Catches O(n^2) regressions independently of machine speed: with a
        linear implementation the per-line query cost of the large scenario
        stays close to the small one (it usually *drops*, as fixed costs are
        amortized).
        """
        if not PERF_STRICT or not getattr(self, "warm", True):
            return
        simple = self._perf_results[(simple_scenario, step)]
        complex_ = self._perf_results[(complex_scenario, step)]
        per_line_simple = simple["queries"] / simple["lines"]
        per_line_complex = complex_["queries"] / complex_["lines"]
        self.assertLessEqual(
            per_line_complex,
            per_line_simple * max_factor,
            "Non-linear query scaling in step '%s': %.1f queries/line with "
            "%d lines vs %.1f queries/line with %d lines (max factor %.2f). "
            "This usually means a per-line loop now triggers whole-recordset "
            "work (O(n^2))."
            % (
                step,
                per_line_complex,
                complex_["lines"],
                per_line_simple,
                simple["lines"],
                max_factor,
            ),
        )
