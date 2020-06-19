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
        inverse="_inverse_city_id",
    )

    @api.multi
    def _compute_l10n_br_data(self):
        """ Read the l10n_br specific functional fields. """

        for c in self:
            c.legal_name = c.partner_id.legal_name
            c.cnpj_cpf = c.partner_id.cnpj_cpf
            c.street_number = c.partner_id.street_number
            c.district = c.partner_id.district
            c.city_id = c.partner_id.city_id
            c.inscr_est = c.partner_id.inscr_est
            c.inscr_mun = c.partner_id.inscr_mun
            c.suframa = c.partner_id.suframa
            state_tax_number_ids = self.env["state.tax.numbers"]
            for state_tax_number in c.partner_id.state_tax_number_ids:
                state_tax_number_ids |= state_tax_number
            c.state_tax_number_ids = state_tax_number_ids
