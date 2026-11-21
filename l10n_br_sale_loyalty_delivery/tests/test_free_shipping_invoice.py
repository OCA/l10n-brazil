# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged

from odoo.addons.l10n_br_sale.hooks import sale_set_journal_in_fiscal_operation
from odoo.addons.l10n_br_stock_account.tests.common import TestBrPickingInvoicingCommon


@tagged("post_install", "-at_install")
class TestFreeShippingInvoice(TestBrPickingInvoicingCommon):
    """A free-shipping reward on an order invoiced from the delivery must lower
    the fiscal freight (vFrete) of the delivered product lines, so the invoice
    total matches what the customer paid (the reward line, a service with no
    stock move, is otherwise dropped and the freight stays as a residual)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        companies = cls.env["res.company"].search(
            [("sale_invoicing_policy", "=", "sale_order")]
        )
        companies.sale_invoicing_policy = "stock_picking"
        sale_set_journal_in_fiscal_operation(cls.env)

        cls.fo_venda = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        company = cls.env.company
        sale_journal = cls.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", company.id)], limit=1
        )
        cls.fo_venda.with_company(company).journal_id = sale_journal

        # Cost equals sale price on purpose: when invoicing from the picking a
        # full l10n_br install prices the product line of a sale delivery at
        # the product cost rather than the sale price. This test only checks
        # that the free-shipping reward is folded into the fiscal freight, not
        # which base price the stack bills, so keeping cost == price makes the
        # asserted totals hold either way.
        cls.product = cls.env["product.product"].create(
            {
                "name": "Free Shipping Test Product",
                "type": "consu",
                "is_storable": True,
                "invoice_policy": "delivery",
                "lst_price": 100.0,
                "standard_price": 100.0,
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "delivery_type": "fixed",
                "fixed_price": 30.0,
                "product_id": cls.env["product.product"]
                .create({"name": "Test Freight", "type": "service"})
                .id,
            }
        )
        cls.program = cls.env["loyalty.program"].create(
            {
                "name": "Free Shipping Code",
                "program_type": "promo_code",
                "trigger": "with_code",
                "applies_on": "current",
                "rule_ids": [
                    Command.create(
                        {"mode": "with_code", "code": "FREESHIP", "minimum_amount": 0}
                    )
                ],
                "reward_ids": [Command.create({"reward_type": "shipping"})],
            }
        )

    def _apply_code(self, order, code):
        rewards = order._try_apply_code(code)
        self.assertFalse(rewards.get("error"), rewards.get("error"))
        for coupon, coupon_rewards in rewards.items():
            order._apply_program_reward(coupon_rewards, coupon)
        order._update_programs_and_rewards()

    def _reward_line(self, order):
        return order.order_line.filtered(
            lambda ln: ln.reward_id.reward_type == "shipping"
        )

    def _create_order(self, qty=2):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "fiscal_operation_id": self.fo_venda.id,
                "order_line": [
                    Command.create(
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": qty,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": self.product.lst_price,
                            "fiscal_operation_id": self.fo_venda.id,
                        }
                    )
                ],
            }
        )

    def _deliver_and_invoice(self, order):
        order.action_confirm()
        self.assertEqual(len(order.picking_ids), 1, "No picking created")
        self.picking_move_state(order.picking_ids)
        return self.create_invoice_wizard(order.picking_ids)

    def test_free_shipping_folded_as_freight_value(self):
        order = self._create_order(qty=2)
        order.set_delivery_line(self.carrier, 30.0)
        self.assertAlmostEqual(order.amount_freight_value, 30.0)
        self._apply_code(order, "FREESHIP")

        reward = self._reward_line(order)
        self.assertAlmostEqual(reward.price_subtotal, -30.0)
        # 200 products + 30 freight - 30 reward
        self.assertAlmostEqual(order.amount_total, 200.0)
        self.assertTrue(reward._loyalty_folds_into_invoice())

        invoice = self._deliver_and_invoice(order)
        self.assertTrue(invoice)
        self.assertFalse(
            invoice.invoice_line_ids.filtered(lambda ln: ln.price_subtotal < 0),
            "Free shipping must not be a negative invoice line",
        )
        # Freight waived -> no freight left on the invoice, total == products.
        product_lines = invoice.invoice_line_ids.filtered(
            lambda ln: ln.display_type == "product"
        )
        self.assertAlmostEqual(sum(product_lines.mapped("freight_value")), 0.0)
        self.assertAlmostEqual(invoice.amount_total, order.amount_total)

    def test_free_shipping_no_residual_and_fully_invoiced(self):
        order = self._create_order(qty=2)
        order.set_delivery_line(self.carrier, 30.0)
        self._apply_code(order, "FREESHIP")
        reward = self._reward_line(order)

        invoice = self._deliver_and_invoice(order)
        invoice.action_post()
        register = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create({})
        )
        register.action_create_payments()

        self.assertEqual(invoice.payment_state, "paid")
        self.assertAlmostEqual(invoice.amount_residual, 0.0)
        self.assertAlmostEqual(reward.qty_invoiced, reward.product_uom_qty)
        self.assertEqual(order.invoice_status, "invoiced")
        self.assertFalse(order._get_invoiceable_lines())
