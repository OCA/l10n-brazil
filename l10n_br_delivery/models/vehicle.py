# Copyright (C) 2010  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class CarrierVehicle(models.Model):
    _name = "l10n_br_delivery.carrier.vehicle"
    _description = "Carrier Vehicle"

    name = fields.Char(required=True)

    description = fields.Char()

    plate = fields.Char(string="Placa")

    driver = fields.Char()

    rntc_code = fields.Char(string="ANTT Code")

    country_id = fields.Many2one(
        comodel_name="res.country",
        string="Country",
    )

    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="State",
        domain="[('country_id', '=', country_id)]",
    )

    city_id = fields.Many2one(
        comodel_name="res.city",
        string="City",
        domain="[('state_id', '=', state_id)]",
    )

    active = fields.Boolean()

    manufacture_year = fields.Char(string="Ano de Fabricacao")

    model_year = fields.Char(string="Ano do Modelo")

    type = fields.Selection(
        selection=[("bau", "Caminhao Bau")],
        string="Model Type",
    )

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Carrier",
        index=True,
        ondelete="cascade",
    )
