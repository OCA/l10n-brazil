# Copyright (C) 2010  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class CarrierVehicle(models.Model):
    _name = 'l10n_br_delivery.carrier.vehicle'
    _description = 'Carrier Vehicle'

    name = fields.Char(
        string='Name',
        required=True,
        size=32
    )

    description = fields.Char(
        string='Description',
        size=132,
    )

    plate = fields.Char(
        string='Placa',
        size=7,
    )

    driver = fields.Char(
        string='Driver',
        size=64,
    )

    rntc_code = fields.Char(
        string='ANTT Code',
        size=32,
    )

    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
    )

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State',
        domain="[('country_id', '=', country_id)]",
    )

    city_id = fields.Many2one(
        comodel_name='res.city',
        string='City',
        domain="[('state_id', '=', state_id)]",
    )

    active = fields.Boolean(
        string='Active',
    )

    manufacture_year = fields.Char(
        string='Ano de Fabricação',
        size=4,
    )

    model_year = fields.Char(
        string='Ano do Modelo',
        size=4,
    )

    type = fields.Selection(
        selection=[('bau', 'Caminhão Baú')],
        string='Model Type',
    )

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier',
        index=True,
        ondelete='cascade',
    )
