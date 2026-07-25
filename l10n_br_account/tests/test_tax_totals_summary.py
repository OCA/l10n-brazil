# Copyright 2026-TODAY Cristiano Mafra Junior
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from unittest.mock import patch

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTaxTotalsSummary(TransactionCase):
    """
    Regression tests for AccountTax._get_tax_totals_summary().

    The Brazilian override shifts the base amount by the delta between the
    fiscal document total and the generic tax engine total (e.g. ICMS-ST
    addbacks not reflected by the generic engine). These tests protect the
    arithmetic invariants of that override: base + tax + cash rounding must
    still equal the total, and once the base is shifted, the "same tax base"
    shortcut must not hide the per tax group bases anymore.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.env.user.company_id = cls.company
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        # With a high enough price, this product triggers ICMS, IPI, PIS
        # and COFINS at once (see test_tax_computation.py).
        cls.product = cls.env.ref("l10n_br_fiscal.customized_development_sale")
        cls.fo_venda = cls.env.ref("l10n_br_fiscal.fo_venda")

    def _create_invoice(self, price_unit, cash_rounding=None):
        vals = {
            "move_type": "out_invoice",
            "partner_id": self.partner.id,
            "company_id": self.company.id,
            "fiscal_operation_id": self.fo_venda.id,
            "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
            "invoice_line_ids": [
                Command.create(
                    {
                        "product_id": self.product.id,
                        "quantity": 1.0,
                        "price_unit": price_unit,
                        "fiscal_operation_id": self.fo_venda.id,
                        "fiscal_operation_line_id": self.fo_venda.line_ids[0].id,
                    }
                )
            ],
        }
        if cash_rounding:
            vals["invoice_cash_rounding_id"] = cash_rounding.id
        return self.env["account.move"].create(vals)

    def test_delta_keeps_cash_rounding_and_flags_same_tax_base(self):
        cash_rounding = self.env["account.cash.rounding"].create(
            {
                "name": "Test cash rounding",
                "rounding": 1.0,
                "strategy": "biggest_tax",
                "rounding_method": "HALF-UP",
            }
        )
        invoice = self._create_invoice(price_unit=1000.33, cash_rounding=cash_rounding)

        # Baseline sanity check: without any Brazilian delta, base + tax +
        # cash rounding must already close on the total.
        invoice.invalidate_recordset(["tax_totals"])
        baseline = invoice.tax_totals
        self.assertAlmostEqual(
            baseline["base_amount_currency"]
            + baseline["tax_amount_currency"]
            + baseline.get("cash_rounding_base_amount_currency", 0.0),
            baseline["total_amount_currency"],
            places=2,
        )

        # Force a Brazilian fiscal delta (e.g. an ICMS-ST addback not
        # reflected by the generic tax engine) to exercise the override's
        # correction path together with cash rounding.
        forced_total = invoice.amount_total + 3.21
        with patch(
            "odoo.addons.l10n_br_account.models.account_move_line."
            "AccountMoveLine._get_total_for_tax_totals",
            return_value=forced_total,
        ):
            invoice.invalidate_recordset(["tax_totals"])
            tax_totals = invoice.tax_totals

        cash_rounding_base_amount = tax_totals.get("cash_rounding_base_amount", 0.0)

        # The BR delta must not swallow the cash rounding contribution.
        self.assertAlmostEqual(
            tax_totals["base_amount"]
            + tax_totals["tax_amount"]
            + cash_rounding_base_amount,
            tax_totals["total_amount"],
            places=2,
        )
        self.assertAlmostEqual(
            tax_totals["total_amount_currency"], forced_total, places=2
        )

        # Once the base is shifted, it no longer matches the (untouched) per
        # tax group bases, so the widget must not hide them anymore.
        self.assertFalse(tax_totals["same_tax_base"])

        # Every subtotal must keep the core's chained identity: base +
        # accumulated tax so far.
        accumulated_tax_amount = 0.0
        for subtotal in tax_totals["subtotals"]:
            self.assertAlmostEqual(
                subtotal["base_amount"],
                tax_totals["base_amount"] + accumulated_tax_amount,
                places=2,
            )
            accumulated_tax_amount += subtotal["tax_amount"]

    def test_zero_delta_does_not_touch_same_tax_base(self):
        """When the fiscal total already matches the generic engine total,
        the override must be a no-op (early exit), leaving the core's own
        'same_tax_base' computation untouched."""
        invoice = self._create_invoice(price_unit=1000.0)

        invoice.invalidate_recordset(["tax_totals"])
        with patch(
            "odoo.addons.l10n_br_account.models.account_move_line."
            "AccountMoveLine._get_total_for_tax_totals",
            return_value=invoice.amount_total,
        ):
            invoice.invalidate_recordset(["tax_totals"])
            tax_totals = invoice.tax_totals

        self.assertAlmostEqual(
            tax_totals["base_amount"] + tax_totals["tax_amount"],
            tax_totals["total_amount"],
            places=2,
        )
