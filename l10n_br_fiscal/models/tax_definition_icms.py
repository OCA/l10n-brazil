# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class TaxDefinitionICMS(models.Model):
    _inherit = "l10n_br_fiscal.tax.definition"

    icms_regulation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.icms.regulation",
        string="ICMS Regulation")

    state_from_id = fields.Many2one(
        comodel_name='res.country.state',
        string='From State',
        domain=[('country_id.code', '=', 'BR')])

    state_to_id = fields.Many2one(
        comodel_name='res.country.state',
        string='To State',
        domain=[('country_id.code', '=', 'BR')])
