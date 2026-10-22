# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


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
