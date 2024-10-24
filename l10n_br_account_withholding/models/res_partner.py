# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):

    _inherit = "res.partner"

    # TODO: Add WH fields for State and Country
    wh_cityhall = fields.Boolean(string="Is City Hall?")

    _sql_constraints = [
        (
            "unique_wh_cityhall",
            "UNIQUE(city_id, wh_cityhall)",
            "Only one partner with the same City Hall can exist in the same city.",
        ),
    ]
