# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Performance baseline + regression guard for the BR SO -> invoice flow.

Complements the l10n_br_account Form-path test with the pure ORM path used
by batch flows and integrations: ``create()`` the sale order with N lines
(letting the fiscal operation line mapping be computed), confirm it, create
the invoices and post them.

Baseline (calibration):
    date=2026-07-17 sha=683173c078 (OCA 16.0) db=perf-oca
    (clean: l10n_br_account,l10n_br_sale,l10n_br_coa_generic,l10n_br_coa_simple + demo)
    so_create:       simple=149q (0.09s) complex=379q (0.49s)
    so_confirm:      simple=14q  (0.01s) complex=41q  (0.02s)
    create_invoices: simple=162q (0.20s) complex=409q (0.88s)
    invoice_post:    simple=61q  (0.05s) complex=81q  (0.15s)

Recalibrated after dropping clear_caches() from move/aml unlink:
    so_create:       simple=116q complex=360q
    so_confirm:      simple=10q  complex=39q
    create_invoices: simple=129q complex=380q
    invoice_post:    simple=29q  complex=61q

Limits are calibrated against the OCA CI environment (canonical reference:
the full localization is installed there, which legitimately costs more
queries than a minimal database — e.g. l10n_br_sale_stock creates pickings
on SO confirm). OCA CI, all patches applied (runs are deterministic across
the Odoo/OCB jobs, spread <=1q):
    so_create:       simple=128q complex=422q
    so_confirm:      simple=157q complex=1113q
    create_invoices: simple=145q complex=423q
    invoice_post:    simple=56q  complex=140q
Limits = CI measured * 1.15 rounded up; minimal-db runs stay far below.
Time is logged, never asserted.

Opt-in: this suite is tagged ``-standard`` so it is EXCLUDED from the default
test run (``inv test`` / OCA CI). Run it explicitly with
``--test-tags l10n_br_performance``.
"""

from odoo.tests.common import tagged, warmup

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon
from odoo.addons.l10n_br_account.tests.perf_common import PerfMixin

LINES_SIMPLE = 2
LINES_COMPLEX = 30

QUERY_LIMIT_SO_CREATE_SIMPLE = 150
QUERY_LIMIT_SO_CREATE_COMPLEX = 490
QUERY_LIMIT_SO_CONFIRM_SIMPLE = 185
QUERY_LIMIT_SO_CONFIRM_COMPLEX = 1280
QUERY_LIMIT_CREATE_INVOICES_SIMPLE = 170
QUERY_LIMIT_CREATE_INVOICES_COMPLEX = 490
QUERY_LIMIT_INVOICE_POST_SIMPLE = 65
QUERY_LIMIT_INVOICE_POST_COMPLEX = 165

SCALING_MAX_FACTOR = 1.5

STEPS = ("so_create", "so_confirm", "create_invoices", "invoice_post")


@tagged("-standard", "post_install", "-at_install", "l10n_br_performance")
class TestL10nBrSalePerformance(PerfMixin, AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()
        cls.fo_venda = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fo_venda_venda = cls.env.ref("l10n_br_fiscal.fo_venda_venda")
        # Invoice on ordered quantities: makes the SO invoiceable right after
        # confirmation, without simulating deliveries.
        (cls.product_a | cls.product_b).invoice_policy = "order"
        company = cls.company_data["company"]
        # Fallback used by l10n_br_sale._prepare_invoice() so the generated
        # invoice carries a fiscal document (the expensive, realistic path).
        company.document_type_id = cls.env.ref("l10n_br_fiscal.document_55")
        # Deterministic pricing in company currency (no pricelist noise).
        cls.pricelist_brl = cls.env["product.pricelist"].create(
            {
                "name": "PERF BRL pricelist",
                "currency_id": company.currency_id.id,
                "company_id": company.id,
            }
        )

    def _make_sale_order(self, line_count):
        pool = [self.product_a, self.product_b]
        lines = []
        for index in range(line_count):
            product = pool[index % 2]
            lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_qty": 1 + index % 3,
                        "price_unit": 100.0 + index,
                        # sale.order.line redefines these mixin fields without
                        # compute/default: on the pure ORM path they must be
                        # given explicitly (same as demo data / integrations).
                        "fiscal_operation_id": self.fo_venda.id,
                        "fiscal_operation_line_id": self.fo_venda_venda.id,
                    },
                )
            )
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
                "pricelist_id": self.pricelist_brl.id,
                "fiscal_operation_id": self.fo_venda.id,
                "order_line": lines,
            }
        )

    def _run_flow(self, scenario, line_count):
        with self._measure(scenario, "so_create", line_count):
            order = self._make_sale_order(line_count)
        with self._measure(scenario, "so_confirm", line_count):
            order.action_confirm()
        # Outside measurement: make every line invoiceable regardless of the
        # product invoicing policy (same approach as
        # test_l10n_br_sale_lp.test_partial_invoice_fiscal_quantity).
        for line in order.order_line:
            line.qty_delivered = line.product_uom_qty
        self.env.flush_all()
        with self._measure(scenario, "create_invoices", line_count):
            order._create_invoices(final=True)
        with self._measure(scenario, "invoice_post", line_count):
            order.invoice_ids.action_post()
        return order

    @warmup
    def test_sale_to_invoice_performance(self):
        self._run_flow("simple", LINES_SIMPLE)
        self._run_flow("complex", LINES_COMPLEX)

        limits = {
            ("simple", "so_create"): QUERY_LIMIT_SO_CREATE_SIMPLE,
            ("complex", "so_create"): QUERY_LIMIT_SO_CREATE_COMPLEX,
            ("simple", "so_confirm"): QUERY_LIMIT_SO_CONFIRM_SIMPLE,
            ("complex", "so_confirm"): QUERY_LIMIT_SO_CONFIRM_COMPLEX,
            ("simple", "create_invoices"): QUERY_LIMIT_CREATE_INVOICES_SIMPLE,
            ("complex", "create_invoices"): QUERY_LIMIT_CREATE_INVOICES_COMPLEX,
            ("simple", "invoice_post"): QUERY_LIMIT_INVOICE_POST_SIMPLE,
            ("complex", "invoice_post"): QUERY_LIMIT_INVOICE_POST_COMPLEX,
        }
        for (scenario, step), limit in limits.items():
            self._assert_queries(scenario, step, limit)
        for step in STEPS:
            self._assert_scaling(step, "simple", "complex", SCALING_MAX_FACTOR)
