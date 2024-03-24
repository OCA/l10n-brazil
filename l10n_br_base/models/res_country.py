# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class Country(models.Model):
    _inherit = "res.country"

    bc_code = fields.Char(
        string="BC Code",
        size=4,
        unaccent=False,
    )

    ibge_code = fields.Char(
        string="IBGE Code",
        size=4,
        unaccent=False,
    )

    siscomex_code = fields.Char(
        size=3,
        unaccent=False,
    )

    nationality_code = fields.Char(
        size=2,
        unaccent=False,
    )
