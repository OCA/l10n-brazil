# Copyright (C) 2010  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

VEHICLE_WHEEL_TYPE = [
    ("01", "Truck"),
    ("02", "Toco"),
    ("03", "Cavalo Mecânico"),
    ("04", "VAN"),
    ("05", "Utilitário"),
    ("06", "Outros"),
]

VEHICLE_BODY_TYPE = [
    ("00", "Não aplicável"),
    ("01", "Aberta"),
    ("02", "Fechada/Baú"),
    ("03", "Granelera"),
    ("04", "Porta Container"),
    ("05", "Sider"),
]


class CarrierVehicle(models.Model):
    _name = "l10n_br_delivery.carrier.vehicle"
    _description = "Carrier Vehicle"

    name = fields.Char(
        required=True,
        size=32,
        unaccent=False,
    )

    description = fields.Char(
        size=132,
        unaccent=False,
    )

    owner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Owner",
    )

    plate = fields.Char(
        string="Placa",
        size=7,
    )

    vehicle_code = fields.Char(
        size=10,
    )

    renavam = fields.Char(
        string="RENAVAM",
        size=11,
    )

    driver = fields.Char(
        size=64,
        unaccent=False,
    )

    rntc_code = fields.Char(
        string="ANTT Code",
        size=32,
    )

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

    manufacture_year = fields.Char(
        string="Ano de Fabricação",
        size=4,
    )

    model_year = fields.Char(
        string="Ano do Modelo",
        size=4,
    )

    type = fields.Selection(
        selection=[("bau", "Caminhão Baú")],
        string="Model Type",
    )

    wheel_type = fields.Selection(
        selection=VEHICLE_WHEEL_TYPE,
    )

    body_type = fields.Selection(
        selection=VEHICLE_BODY_TYPE,
    )

    tara = fields.Char(
        string="Tara (KG)",
    )

    capacity_kg = fields.Char(
        string="Capacity (KG)",
    )

    capacity_m3 = fields.Char(
        string="Capacity (M3)",
    )

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Carrier",
        index=True,
        ondelete="cascade",
    )
