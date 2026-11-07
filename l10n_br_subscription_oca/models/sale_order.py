# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def create_subscription(self, lines, subscription_tmpl):
        # subscription_oca builds the subscription values inline: hand the
        # fiscal operation of the order over as the default of the new one.
        order = self.with_context(
            default_fiscal_operation_id=self.fiscal_operation_id.id
        )
        return super(SaleOrder, order).create_subscription(lines, subscription_tmpl)
