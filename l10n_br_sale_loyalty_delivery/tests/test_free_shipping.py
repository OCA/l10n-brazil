# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form, TransactionCase


class TestFreeShipping(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env.ref("l10n_br_base.res_partner_kmee")
        cls.product = cls.env.ref("product.product_delivery_01")
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "delivery_type": "fixed",
                "fixed_price": 25.0,
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
                    (
                        0,
                        0,
                        {
                            "mode": "with_code",
                            "code": "FREESHIP",
                            "minimum_amount": 0,
                        },
                    )
                ],
                "reward_ids": [(0, 0, {"reward_type": "shipping"})],
            }
        )

    def _create_order(self):
        so_form = Form(self.env["sale.order"])
        so_form.partner_id = self.partner
        with so_form.order_line.new() as line:
            line.product_id = self.product
            line.product_uom_qty = 1.0
            line.price_unit = 100.0
        order = so_form.save()
        order.set_delivery_line(self.carrier, 25.0)
        return order

    def _apply_code(self, order, code):
        rewards = order._try_apply_code(code)
        self.assertFalse(rewards.get("error"))
        for coupon, coupon_rewards in rewards.items():
            order._apply_program_reward(coupon_rewards, coupon)
        order._update_programs_and_rewards()

    def _reward_line(self, order):
        return order.order_line.filtered(
            lambda line: line.reward_id.reward_type == "shipping"
        )

    def test_free_shipping_discounts_freight_value(self):
        order = self._create_order()
        self.assertFalse(order.order_line.filtered("is_delivery"))
        self.assertAlmostEqual(order.amount_freight_value, 25.0)
        self.assertAlmostEqual(order.amount_total, 125.0)

        self._apply_code(order, "FREESHIP")

        self.assertAlmostEqual(self._reward_line(order).price_unit, -25.0)
        self.assertAlmostEqual(order.amount_freight_value, 25.0)
        self.assertAlmostEqual(order.amount_total, 100.0)

    def test_free_shipping_max_discount(self):
        self.program.reward_ids.discount_max_amount = 10.0
        order = self._create_order()

        self._apply_code(order, "FREESHIP")

        self.assertAlmostEqual(self._reward_line(order).price_unit, -10.0)
        self.assertAlmostEqual(order.amount_total, 115.0)

    def test_free_shipping_follows_freight_change(self):
        order = self._create_order()
        self._apply_code(order, "FREESHIP")

        order.set_delivery_line(self.carrier, 40.0)
        order._update_programs_and_rewards()

        self.assertAlmostEqual(self._reward_line(order).price_unit, -40.0)
        self.assertAlmostEqual(order.amount_total, 100.0)
