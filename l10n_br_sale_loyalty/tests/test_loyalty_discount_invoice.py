# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged

from odoo.addons.l10n_br_sale.hooks import sale_set_journal_in_fiscal_operation
from odoo.addons.l10n_br_stock_account.tests.common import TestBrPickingInvoicingCommon


@tagged("post_install", "-at_install")
class TestLoyaltyDiscountInvoice(TestBrPickingInvoicingCommon):
    """A loyalty discount reward on an order invoiced from the delivery must
    become fiscal discount (vDesc) on the delivered product lines, so a single
    valid invoice is issued whose total matches what the customer paid.

    Without this, the reward line (a service with no stock move) is dropped by
    the picking-based invoice: the invoice keeps the full price, the payment of
    the discounted total only covers part of it, and the invoice stays
    'partially paid' (while a negative reward line would be an invalid NF-e
    item).
    """

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

        # The sale fiscal operation needs a journal for the test company so the
        # invoice can be generated from the picking (the base class only maps
        # journals for the "remessa" operations it uses).
        company = cls.env.company
        sale_journal = cls.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", company.id)], limit=1
        )
        cls.fo_venda.with_company(company).journal_id = sale_journal

        # Cost equals sale price on purpose. When invoicing from the picking,
        # the unit price of the invoice line comes from the stock move, and in
        # a full l10n_br install the move of a sale delivery resolves to the
        # product cost (l10n_br_stock_account prices an outgoing move at
        # ``standard_price``) rather than the sale price. This test only checks
        # that the reward is folded into the fiscal discount, not which base
        # price the stack bills, so keeping cost == price makes the asserted
        # totals hold either way.
        cls.product = cls.env["product.product"].create(
            {
                "name": "Loyalty Test Product",
                "type": "consu",
                "is_storable": True,
                "invoice_policy": "delivery",
                "lst_price": 100.0,
                "standard_price": 100.0,
            }
        )

        cls.program = cls.env["loyalty.program"].create(
            {
                "name": "10% OFF Code",
                "program_type": "promo_code",
                "trigger": "with_code",
                "applies_on": "current",
                "rule_ids": [
                    Command.create(
                        {
                            "mode": "with_code",
                            "code": "TENOFF",
                            "minimum_amount": 0,
                        }
                    )
                ],
                "reward_ids": [
                    Command.create(
                        {
                            "reward_type": "discount",
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        }
                    )
                ],
            }
        )

    def _apply_code(self, order, code):
        rewards = order._try_apply_code(code)
        self.assertFalse(rewards.get("error"), rewards.get("error"))
        for coupon, coupon_rewards in rewards.items():
            order._apply_program_reward(coupon_rewards, coupon)
        order._update_programs_and_rewards()

    def _create_order(self, qty=2):
        order = self.env["sale.order"].create(
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
        return order

    def _product_line(self, order):
        return order.order_line.filtered(lambda ln: not ln.is_reward_line)

    def _reward_line(self, order):
        return order.order_line.filtered(
            lambda ln: ln.reward_id.reward_type == "discount"
        )

    def _deliver_and_invoice(self, order):
        order.action_confirm()
        self.assertEqual(len(order.picking_ids), 1, "No picking created")
        self.picking_move_state(order.picking_ids)
        invoice = self.create_invoice_wizard(order.picking_ids)
        return invoice

    def test_discount_reward_folded_as_fiscal_discount(self):
        order = self._create_order(qty=2)
        self._apply_code(order, "TENOFF")

        reward = self._reward_line(order)
        product_line = self._product_line(order)
        self.assertTrue(reward, "No discount reward line created")
        # 10% of 200.0
        self.assertAlmostEqual(reward.price_subtotal, -20.0)
        self.assertAlmostEqual(order.amount_total, 180.0)
        # sale_loyalty_order_line_link maps the reward to the discounted line
        self.assertIn(reward, product_line.reward_line_ids)
        self.assertIn(product_line, reward.reward_discounted_line_ids)
        self.assertTrue(reward._loyalty_folds_into_invoice())

        invoice = self._deliver_and_invoice(order)
        self.assertTrue(invoice, "No invoice created from the delivery")

        # The reward is not a separate (negative) invoice line...
        self.assertFalse(
            invoice.invoice_line_ids.filtered(lambda ln: ln.price_subtotal < 0),
            "Discount must not be a negative invoice line",
        )
        # ...it is the fiscal discount of the product line(s).
        product_inv_lines = invoice.invoice_line_ids.filtered(
            lambda ln: ln.display_type == "product"
        )
        self.assertAlmostEqual(sum(product_inv_lines.mapped("discount_value")), 20.0)
        # The invoice total matches the discounted order total.
        self.assertAlmostEqual(invoice.amount_total, order.amount_total)

    def test_no_residual_after_payment(self):
        order = self._create_order(qty=2)
        self._apply_code(order, "TENOFF")
        invoice = self._deliver_and_invoice(order)
        invoice.action_post()

        self.assertAlmostEqual(invoice.amount_total, 180.0)
        register = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create({})
        )
        register.action_create_payments()
        self.assertEqual(invoice.payment_state, "paid")
        self.assertAlmostEqual(invoice.amount_residual, 0.0)

    def test_order_fully_invoiced_no_second_document(self):
        order = self._create_order(qty=2)
        self._apply_code(order, "TENOFF")
        reward = self._reward_line(order)

        invoice = self._deliver_and_invoice(order)
        invoice.action_post()

        # The reward line counts as invoiced even though it has no invoice line
        # of its own, so the order is fully invoiced and its invoice button
        # would not emit the discount again as a second (negative) document.
        self.assertAlmostEqual(reward.qty_invoiced, reward.product_uom_qty)
        self.assertEqual(order.invoice_status, "invoiced")
        self.assertFalse(order._get_invoiceable_lines())

    def test_non_discount_reward_folds_into_nothing(self):
        """In the base module only discount rewards fold; any other reward
        type contributes no fiscal amount, so it is invoiced the regular way
        and the fold is a no-op."""
        gift = self.env["product.product"].create(
            {"name": "Gift", "type": "consu", "lst_price": 0.0}
        )
        self.env["loyalty.program"].create(
            {
                "name": "Free Gift Code",
                "program_type": "promo_code",
                "trigger": "with_code",
                "applies_on": "current",
                "rule_ids": [
                    Command.create(
                        {"mode": "with_code", "code": "GIFT", "minimum_amount": 0}
                    )
                ],
                "reward_ids": [
                    Command.create(
                        {
                            "reward_type": "product",
                            "reward_product_id": gift.id,
                            "reward_product_qty": 1,
                        }
                    )
                ],
            }
        )
        order = self._create_order(qty=2)
        self._apply_code(order, "GIFT")
        reward = order.order_line.filtered(
            lambda ln: ln.reward_id.reward_type == "product"
        )
        self.assertTrue(reward, "No product reward line created")
        self.assertEqual(reward._loyalty_reward_fiscal_fold(), {})
        self.assertFalse(reward._loyalty_folds_into_invoice())
        # apply_fold short-circuits when the reward folds into nothing.
        self.env["stock.invoice.onshipping"]._loyalty_apply_fold(
            reward, [{"discount_value": 0.0}]
        )

    def test_x2m_ids_parses_set_and_link_commands(self):
        """The reward-line id extraction accepts SET and LINK commands and
        ignores anything else."""
        ids = self.env["stock.invoice.onshipping"]._loyalty_x2m_ids(
            [
                (Command.SET, 0, [1, 2]),
                (Command.LINK, 3),
                "not-a-command",
                (Command.CREATE, 0, {"name": "x"}),
            ]
        )
        self.assertEqual(sorted(ids), [1, 2, 3])

    def test_fold_rewards_without_orders_is_noop(self):
        """With no invoice line carrying a sale line there is no order to fold,
        so folding returns without touching anything."""
        self.env["stock.invoice.onshipping"]._fold_loyalty_rewards(
            {"invoice_line_ids": []}
        )

    def test_apply_fold_splits_evenly_without_weights(self):
        """When the target lines carry no weighting amount, the folded total is
        spread evenly across them."""
        order = self._create_order(qty=2)
        self._apply_code(order, "TENOFF")
        reward = self._reward_line(order)
        targets = [{"price_unit": 0.0, "quantity": 0.0}]
        self.env["stock.invoice.onshipping"]._loyalty_apply_fold(reward, targets)
        self.assertAlmostEqual(targets[0]["discount_value"], 20.0)
