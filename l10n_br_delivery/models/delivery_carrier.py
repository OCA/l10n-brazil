# Copyright (C) 2010  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class Carrier(models.Model):
    _inherit = "delivery.carrier"

    antt_code = fields.Char(
        string="Codigo ANTT",
        size=32,
    )

    vehicle_ids = fields.One2many(
        comodel_name="l10n_br_delivery.carrier.vehicle",
        inverse_name="carrier_id",
        string="Vehicles",
    )

    # FIXME: For now we are going to overwrite this method but this needs
    # to be evaluated further.
    def _get_price_available(self, order):
        self.ensure_one()
        self = self.sudo()
        order = order.sudo()
        total = weight = volume = quantity = 0
        total_delivery = 0.0
        for line in order.order_line:
            if line.state == "cancel":
                continue
            if line.is_delivery:
                total_delivery += line.price_total
            if not line.product_id or line.is_delivery:
                continue
            if line.product_id.type == "service":
                continue
            qty = line.product_uom._compute_quantity(
                line.product_uom_qty, line.product_id.uom_id
            )
            weight += (line.product_id.weight or 0.0) * qty
            volume += (line.product_id.volume or 0.0) * qty
            quantity += qty
        total = (order.amount_total or 0.0) - total_delivery

        # Solves free shipping calculation problem when deducting
        # the shipping value from the total amount
        if order.company_id.country_id.code == "BR":
            total = (order.amount_total or 0.0) - order.amount_freight_value

        total = self._compute_currency(order, total, "pricelist_to_company")

        return self._get_price_from_picking(total, weight, volume, quantity)
