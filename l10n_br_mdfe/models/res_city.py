# Copyright 2025 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ResCity(models.Model):
    _inherit = "res.city"
    _mdfe_search_keys = ["ibge_code"]
