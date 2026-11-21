# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    melhorenvio_order_id = fields.Char(
        string="Melhor Envio Shipment ID", readonly=True, copy=False
    )
    melhorenvio_protocol = fields.Char(
        string="Melhor Envio Protocol", readonly=True, copy=False
    )
    melhorenvio_status = fields.Char(
        string="Melhor Envio Status", readonly=True, copy=False
    )
    melhorenvio_label_url = fields.Char(
        string="Melhor Envio Label", readonly=True, copy=False
    )

    def action_melhorenvio_buy_label(self):
        for picking in self:
            if picking.delivery_type != "melhorenvio":
                raise UserError(
                    self.env._(
                        "The delivery %(name)s is not shipped through Melhor Envio.",
                        name=picking.name,
                    )
                )
            result = picking.carrier_id._melhorenvio_buy_label(picking)
            picking.carrier_price = result["exact_price"] * (
                1.0 + (picking.carrier_id.margin / 100.0)
            )
            if result["tracking_number"]:
                picking.carrier_tracking_ref = result["tracking_number"]
        return True

    def action_melhorenvio_print_label(self):
        self.ensure_one()
        if not self.melhorenvio_label_url:
            raise UserError(self.env._("Buy the Melhor Envio label first."))
        return {
            "type": "ir.actions.act_url",
            "url": self.melhorenvio_label_url,
            "target": "new",
        }
