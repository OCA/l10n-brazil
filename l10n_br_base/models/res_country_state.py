# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class CountryState(models.Model):
    _inherit = 'res.country.state'

    ibge_code = fields.Char(
        string='Codigo IBGE',
        size=2)
