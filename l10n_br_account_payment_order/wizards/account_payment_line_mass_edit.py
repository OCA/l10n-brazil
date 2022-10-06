# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPaymentLineMassEdit(models.TransientModel):
    _name = "account.payment.line.mass.edit"
    _description = "Wizard for mass editing payment lines"

    order_id = fields.Many2one(
        comodel_name="account.payment.order", string="Payment Order"
    )

    allowedd_payment_way_ids = fields.Many2many(
        comodel_name="account.payment.way",
        related="order_id.payment_mode_id.account_payment_way_ids",
    )

    account_payment_way_id = fields.Many2one(
        comodel_name="account.payment.way",
        string="Payment Way",
        domain="[('id', '=', allowedd_payment_way_ids)]",
    )

    payment_line_ids = fields.Many2many(
        comodel_name="account.payment.line",
        string="Transactions",
        domain="[('order_id', '=', order_id)]",
    )

    def update_payment_lines(self):
        self.ensure_one()
        self.payment_line_ids.payment_way_id = self.account_payment_way_id

    @api.model
    def default_get(self, field_list):
        res = super(AccountPaymentLineMassEdit, self).default_get(field_list)
        context = self.env.context
        assert (
            context.get("active_model") == "account.payment.order"
        ), "active_model should be payment.order"
        assert context.get("active_id"), "Missing active_id in context !"
        order = self.env["account.payment.order"].browse(context["active_id"])
        res.update(
            {
                "order_id": order.id,
            }
        )
        return res
