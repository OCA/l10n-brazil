# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_reward_values_free_shipping(self, reward, coupon, **kwargs):
        """l10n_br_delivery doesn't create a delivery line, the freight is
        kept in amount_freight_value and distributed over the product lines.
        Without a delivery line the core reward would be worth zero."""
        values_list = super()._get_reward_values_free_shipping(reward, coupon, **kwargs)
        if self.order_line.filtered("is_delivery"):
            return values_list
        max_discount = reward.discount_max_amount or float("inf")
        for values in values_list:
            values["price_unit"] = -min(max_discount, self.amount_freight_value)
        return values_list

    def _link_reward_lines(self, programs):
        """Link free-shipping reward lines to the product lines that carry the
        freight, so l10n_br_sale_loyalty folds the reward into their fiscal
        freight value (vFrete) when invoicing from the delivery. The core
        module (sale_loyalty_order_line_link) only links discount and product
        rewards.
        """
        res = super()._link_reward_lines(programs)
        for program in programs:
            if not program.reward_ids.filtered(lambda r: r.reward_type == "shipping"):
                continue
            reward_lines = self.order_line.filtered(
                lambda ln, prog=program: ln.loyalty_program_id == prog
                and ln.reward_id.reward_type == "shipping"
            )
            product_lines = self.order_line.filtered(
                lambda ln: not ln.is_reward_line and not ln.display_type
            )
            if reward_lines and product_lines:
                product_lines.write(
                    {"reward_line_ids": [Command.link(rl.id) for rl in reward_lines]}
                )
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _loyalty_reward_fiscal_fold(self):
        """Fold a free-shipping reward into the fiscal freight (vFrete) of the
        product lines it applies to, so it rides the invoice generated from
        the delivery instead of being dropped as a service line."""
        res = super()._loyalty_reward_fiscal_fold()
        if not res and self.is_reward_line and self.reward_id.reward_type == "shipping":
            return {"freight_value": -abs(self.price_subtotal)}
        return res
