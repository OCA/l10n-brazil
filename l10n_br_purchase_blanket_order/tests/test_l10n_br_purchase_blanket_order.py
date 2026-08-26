# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests.common import TransactionCase


class L10nBrPurchaseBlanketOrderTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.partner = cls.env.ref("base.res_partner_1")
        cls.payment_term = cls.env.ref("account.account_payment_term_immediate")
        cls.payment_term_30_days = cls.env.ref("account.account_payment_term_30days")
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.validity_date = date.today() + timedelta(days=2)
        cls.date_schedule = date.today() + timedelta(days=2)
        cls.cnae_secondary = cls.env.ref("l10n_br_fiscal.cnae_31021")

        cls.product = cls.env.ref("product.product_product_27")
        cls.product_uom = cls.env.ref("uom.product_uom_unit")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")

        cls.company.cnae_secondary_ids = [(6, 0, [cls.cnae_secondary.id])]
        cls.env.company = cls.company

    def _create_blanket_order(self, line_values=None, **extra_values):
        line_vals = {
            "product_id": self.product.id,
            "product_uom": self.product_uom.id,
            "date_schedule": self.date_schedule,
            "original_uom_qty": 20.0,
            "price_unit": 25.0,
            "fiscal_operation_id": self.fiscal_operation.id,
        }
        if line_values:
            line_vals.update(line_values)

        values = {
            "partner_id": self.partner.id,
            "company_id": self.company.id,
            "validity_date": self.validity_date,
            "payment_term_id": self.payment_term.id,
            "fiscal_operation_id": self.fiscal_operation.id,
            "line_ids": [Command.create(line_vals)],
        }
        values.update(extra_values)
        blanket_order = (
            self.env["purchase.blanket.order"].with_company(self.company).create(values)
        )
        blanket_order.sudo().onchange_partner_id()
        return blanket_order

    def _create_wizard(self, blanket_order, blanket_lines=None):
        blanket_lines = blanket_lines or blanket_order.line_ids
        lines = [
            Command.create(
                {
                    "blanket_line_id": line.id,
                    "product_id": line.product_id.id,
                    "date_schedule": line.date_schedule,
                    "remaining_uom_qty": line.remaining_uom_qty,
                    "price_unit": line.price_unit,
                    "product_uom": line.product_uom.id,
                    "qty": line.remaining_uom_qty,
                    "partner_id": line.partner_id.id,
                }
            )
            for line in blanket_lines
        ]

        wizard = (
            self.env["purchase.blanket.order.wizard"]
            .with_context(
                active_id=blanket_order.id,
                active_model="purchase.blanket.order",
            )
            .create(
                {
                    "blanket_order_id": blanket_order.id,
                    "line_ids": lines,
                }
            )
        )
        return wizard

    def test_confirm_and_process_blanket_order(self):
        blanket_order = self._create_blanket_order()
        blanket_order._onchange_fiscal_operation_id()
        blanket_order._amount_all()

        self.assertEqual(
            blanket_order.state,
            "draft",
            "Error: Blanket Order is not in draft state.",
        )
        self.assertEqual(blanket_order.fiscal_operation_id.code, "CP")
        self.assertEqual(blanket_order.fiscal_operation_id.fiscal_type, "purchase")

        blanket_order.sudo().action_confirm()

        self.assertEqual(
            blanket_order.state,
            "open",
            "Error: Blanket Order is not in open state after confirmation.",
        )

        blanket_lines = self.env["purchase.blanket.order.line"].search(
            [("order_id", "=", blanket_order.id)]
        )
        self.assertEqual(len(blanket_lines), 1)
        bo_line = blanket_lines[0]
        self.assertTrue(
            bo_line.fiscal_operation_line_id,
            "Error: Blanket Order line has no fiscal operation line.",
        )
        self.assertTrue(
            bo_line.fiscal_tax_ids,
            "Error: Blanket Order line has no fiscal taxes.",
        )
        expected_account_taxes = bo_line.fiscal_tax_ids.account_taxes(
            user_type="purchase",
            fiscal_operation=bo_line.fiscal_operation_id,
            company=bo_line.company_id,
        )
        self.assertTrue(
            bo_line.taxes_id,
            "Error: Blanket Order line taxes_id was not filled from fiscal taxes.",
        )
        self.assertEqual(bo_line.taxes_id, expected_account_taxes)

        wizard = self._create_wizard(blanket_order)
        result = wizard.create_purchase_order()
        purchase_order_id = result.get("domain", [])[0][2][0]

        self.assertEqual(
            blanket_order.state,
            "done",
            "Error: Blanket Order is not in done state after processing.",
        )

        purchase_order = self.env["purchase.order"].browse(purchase_order_id)

        self.assertEqual(
            purchase_order.state,
            "draft",
            "Error: Purchase Order is not in draft state.",
        )

        for order_line in purchase_order.order_line:
            self.assertTrue(
                order_line.taxes_id,
                "Error: Purchase Order line taxes_id was not filled from blanket.",
            )
            self.assertEqual(order_line.taxes_id, expected_account_taxes)

        purchase_order.button_confirm()

        self.assertEqual(
            purchase_order.state,
            "purchase",
            "Error: Purchase Order is not in purchase state after confirm.",
        )

        self.assertEqual(
            purchase_order.fiscal_operation_id,
            purchase_order.order_line[0].fiscal_operation_id,
        )

    def test_partial_quantity_recomputes_fiscal_amounts(self):
        """A purchase order created from a blanket order line for a partial
        quantity must have its fiscal amounts recomputed for that quantity,
        not copied over from the blanket order line's original quantity.
        """
        blanket_order = self._create_blanket_order()
        blanket_order._onchange_fiscal_operation_id()
        blanket_order._amount_all()
        blanket_order.sudo().action_confirm()

        bo_line = blanket_order.line_ids[0]
        self.assertEqual(bo_line.quantity, 20.0)
        self.assertTrue(bo_line.taxes_id)

        full_price_subtotal = bo_line.price_subtotal
        self.assertTrue(full_price_subtotal)
        partial_qty = 5.0
        wizard = self._create_wizard(blanket_order)
        wizard.line_ids.qty = partial_qty

        result = wizard.create_purchase_order()
        purchase_order = self.env["purchase.order"].browse(result["domain"][0][2][0])
        po_line = purchase_order.order_line[0]
        self.assertEqual(po_line.product_qty, partial_qty)
        expected_subtotal = full_price_subtotal * partial_qty / bo_line.quantity
        self.assertAlmostEqual(po_line.price_subtotal, expected_subtotal, 2)
        self.assertNotAlmostEqual(po_line.price_subtotal, full_price_subtotal, 2)

    def test_prepare_po_line_uses_order_start_without_schedule(self):
        blanket_order = self._create_blanket_order({"date_schedule": False})
        wizard = self._create_wizard(blanket_order)
        vals = wizard._prepare_po_line_vals(wizard.line_ids)

        self.assertEqual(vals["date_planned"], blanket_order.date_start)
        self.assertEqual(vals["quantity"], wizard.line_ids.qty)
        self.assertEqual(vals["fiscal_quantity"], wizard.line_ids.qty)
        self.assertEqual(vals["company_id"], blanket_order.company_id.id)

    def test_prepare_po_vals_rejects_different_fiscal_operations(self):
        blanket_order = self._create_blanket_order()
        wizard = self._create_wizard(blanket_order)
        blanket_line = blanket_order.line_ids

        with self.assertRaises(UserError):
            wizard._prepare_po_vals(
                supplier=self.partner.id,
                currency_id=blanket_order.currency_id.id,
                payment_term_id=blanket_order.payment_term_id.id,
                order_lines=[
                    (
                        0,
                        0,
                        {
                            "fiscal_operation_id": self.env.ref(
                                "l10n_br_fiscal.fo_compras"
                            ).id,
                            "blanket_order_line": blanket_line.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "fiscal_operation_id": self.env.ref(
                                "l10n_br_fiscal.fo_venda"
                            ).id,
                            "blanket_order_line": blanket_line.id,
                        },
                    ),
                ],
            )

    def test_create_purchase_order_rejects_empty_and_excess_quantities(self):
        blanket_order = self._create_blanket_order()
        blanket_order.sudo().action_confirm()

        wizard = self._create_wizard(blanket_order)
        wizard.line_ids.qty = 0.0
        with self.assertRaises(UserError):
            wizard.create_purchase_order()

        wizard = self._create_wizard(blanket_order)
        wizard.line_ids.qty = wizard.line_ids.remaining_uom_qty + 1.0
        with self.assertRaises(UserError):
            wizard.create_purchase_order()

    def test_create_purchase_order_rejects_different_currencies(self):
        first_order = self._create_blanket_order()
        second_order = self._create_blanket_order()
        other_currency = self.env.ref("base.USD")
        if other_currency == first_order.currency_id:
            other_currency = self.env.ref("base.EUR")

        first_order.write({"payment_term_id": self.payment_term.id})
        second_order.write(
            {
                "currency_id": other_currency.id,
                "payment_term_id": self.payment_term_30_days.id,
            }
        )
        first_order.sudo().action_confirm()
        second_order.sudo().action_confirm()

        wizard = self._create_wizard(
            first_order,
            first_order.line_ids | second_order.line_ids,
        )

        with self.assertRaises(UserError):
            wizard.create_purchase_order()

    def test_compute_price_unit_fiscal(self):
        blanket_order = self._create_blanket_order()
        blanket_line = blanket_order.line_ids

        blanket_line.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_compras")
        blanket_line.price_unit = 25.0
        expected_cost_price = self.product._get_tax_included_unit_price(
            blanket_line.company_id,
            blanket_order.currency_id,
            blanket_order.date_start,
            "purchase",
            fiscal_position=blanket_order.fiscal_position_id,
            product_price_unit=blanket_line.price_unit,
            product_currency=blanket_order.currency_id,
        )
        blanket_line._compute_price_unit_fiscal()
        self.assertEqual(blanket_line.price_unit, expected_cost_price)

        blanket_line.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        blanket_line._compute_price_unit_fiscal()
        self.assertEqual(blanket_line.price_unit, self.product.lst_price)

        blanket_line.fiscal_operation_id = False
        blanket_line._compute_price_unit_fiscal()
        self.assertEqual(blanket_line.price_unit, 0.0)

    def test_onchange_product_keeps_taxes_id_from_fiscal(self):
        """Inline tree product onchange must not leave taxes_id empty on BR CoA.

        OCA onchange_product sets taxes_id from supplier_taxes_id (usually empty);
        the BR override re-syncs from fiscal_tax_ids afterwards.
        """
        blanket_order = self._create_blanket_order()
        blanket_order._onchange_fiscal_operation_id()
        line = blanket_order.line_ids[0]
        self.assertTrue(line.fiscal_tax_ids)

        line.taxes_id = False
        line.onchange_product()
        expected = line.fiscal_tax_ids.account_taxes(
            user_type="purchase",
            fiscal_operation=line.fiscal_operation_id,
            company=line.company_id or line.order_id.company_id,
        )
        self.assertTrue(line.taxes_id)
        self.assertEqual(line.taxes_id, expected)

        line._onchange_fiscal_tax_ids()
        self.assertEqual(line.taxes_id, expected)

    def test_withholding_tax_keeps_fiscal_totals(self):
        """Adding a withholding tax must keep totals after form save.

        The line form onchange computes amount_tax_withholding correctly, but
        saving sends fiscal_tax_ids together with *_tax_id. That write used to
        recompute taxes on stale values and persist withholding=0.
        """
        blanket_order = self._create_blanket_order()
        blanket_order._onchange_fiscal_operation_id()
        line = blanket_order.line_ids[0]
        line.write({"original_uom_qty": 1.0, "price_unit": 100.0})

        inss_wh = self.env["l10n_br_fiscal.tax"].search(
            [("tax_domain", "=", "inss_wh")], limit=1
        )
        if not inss_wh:
            self.skipTest("No inss_wh fiscal tax found in demo data.")

        # Reproduce UI save: both fiscal_tax_ids and the specific tax field.
        taxes = line.fiscal_tax_ids | inss_wh
        line.write(
            {
                "inss_wh_tax_id": inss_wh.id,
                "fiscal_tax_ids": [Command.set(taxes.ids)],
            }
        )
        line.invalidate_recordset()

        # Gross stays on the mixin (qty * price_unit), not rebound to untaxed.
        self.assertAlmostEqual(line.price_gross, 100.0, places=2)
        self.assertTrue(
            line.amount_tax_withholding,
            "amount_tax_withholding must persist after saving fiscal taxes.",
        )
        self.assertAlmostEqual(
            line.fiscal_amount_total,
            line.fiscal_amount_untaxed
            + line.fiscal_amount_tax
            - line.amount_tax_withholding,
            places=2,
        )

    def test_cnae_domain(self):
        domain = self.env["purchase.blanket.order.line"]._cnae_domain()
        expected_domain = [
            "|",
            ("id", "in", [self.cnae_secondary.id]),
            ("id", "=", self.company.cnae_main_id.id),
        ]
        self.assertEqual(domain, expected_domain)

    def test_cnae_domain_without_secondary_cnae(self):
        secondary_cnae_ids = self.company.cnae_secondary_ids.ids

        try:
            self.company.cnae_secondary_ids = [Command.clear()]
            domain = self.env["purchase.blanket.order.line"]._cnae_domain()
            self.assertEqual(domain, [])
        finally:
            self.company.cnae_secondary_ids = [Command.set(secondary_cnae_ids)]
