# Copyright 2021 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models

# This is a very simplified copy of the Odoo purchase order model
# in the real life you would inject your xsd spec models into the
# models of the real Odoo purchase module.


class PurchaseOrder(models.Model):
    _name = "fake.purchase.order"
    _description = "Purchase Order"

    READONLY_STATES = {
        "purchase": [("readonly", True)],
        "done": [("readonly", True)],
        "cancel": [("readonly", True)],
    }

    name = fields.Char("Order Reference", required=True, default="New")
    date_order = fields.Datetime(
        "Order Date", required=True, states=READONLY_STATES, default=fields.Datetime.now
    )
    date_approve = fields.Date("Approval Date", readonly=1)
    partner_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
        states=READONLY_STATES,
        change_default=True,
    )
    dest_address_id = fields.Many2one(
        "res.partner", string="Drop Ship Address", states=READONLY_STATES
    )
    currency_id = fields.Many2one(
        "res.currency",
        "Currency",
        required=True,
        default=lambda self: self.env.ref("base.EUR").id,
    )
    state = fields.Selection(
        [
            ("draft", "RFQ"),
            ("sent", "RFQ Sent"),
            ("to approve", "To Approve"),
            ("purchase", "Purchase Order"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        readonly=True,
        index=True,
        copy=False,
        default="draft",
        tracking=True,
    )

    order_line = fields.One2many(
        "fake.purchase.order.line", "order_id", string="Order Lines"
    )


class PurchaseOrderLine(models.Model):
    _name = "fake.purchase.order.line"
    _description = "Purchase Order Line"

    name = fields.Char(string="Description", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    product_qty = fields.Integer(string="Quantity", required=True)
    price_unit = fields.Monetary(string="Unit Price", required=True)
    currency_id = fields.Many2one(
        related="order_id.currency_id", store=True, string="Currency", readonly=True
    )
    order_id = fields.Many2one(
        "fake.purchase.order",
        string="Order Reference",
        index=True,
        required=True,
        ondelete="cascade",
    )
