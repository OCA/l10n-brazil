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
