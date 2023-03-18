# Copyright 2023 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountPaymentOrder(models.Model):

    _inherit = "account.payment.order"

    @api.constrains("payment_line_ids", "state")
    def payment_order_instrument_constraints(self):
        for order in self:
            if order.state == "open":
                move_line_ids = order.payment_line_ids.mapped("move_line_id")
                for payline in order.payment_line_ids:
                    instrument = payline.move_line_id.payment_instrument_id
                    if instrument:
                        inst_mls = move_line_ids.filtered(
                            lambda m: m.payment_instrument_id == instrument
                        )
                        all_inst_mls = self.env["account.move.line"].search(
                            [
                                ("payment_instrument_id", "=", instrument.id),
                            ]
                        )
                        if len(inst_mls) != len(all_inst_mls):
                            raise ValidationError(
                                _(
                                    f"There are more payables with the same payment "
                                    f"instrument as {payline.name} not included in this "
                                    f"order."
                                )
                            )
