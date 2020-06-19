# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class CityTaxationCode(models.Model):

    _name = 'city.taxation.code'
    _description = 'City Taxation Code'

    name = fields.Char(
        string='Description',
    )

    code = fields.Char(
        string='Code',
    )

    service_type_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.service.type',
        string='Service Type',
        domain="[('internal_type', '=', 'normal')]"
    )

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string="State",
        domain=[('country_id.code', '=', 'BR')]
    )

    city_id = fields.Many2one(
        string="City",
        comodel_name="res.city",
        domain="[('state_id', '=', state_id)]",
    )
