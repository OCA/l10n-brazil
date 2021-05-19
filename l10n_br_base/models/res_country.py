# Copyright (C) 2009  Renato Lima - Akretion
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class Country(models.Model):
    _inherit = 'res.country'

    bc_code = fields.Char(
        string='BC Code',
        size=4,
    )

    ibge_code = fields.Char(
        string='IBGE Code',
        size=4,
    )

    siscomex_code = fields.Char(
        string='Siscomex Code',
        size=3,
    )

    nationality_code = fields.Char(
        string='Nationality Code',
        size=2,
    )
