# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def get_subscription_line_values(self):
        values = super().get_subscription_line_values()
        if self.fiscal_operation_id:
            values.update(
                {
                    "fiscal_operation_id": self.fiscal_operation_id.id,
                    "fiscal_operation_line_id": self.fiscal_operation_line_id.id,
                }
            )
        return values
