# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# Copyright 2021 Akretion (Renato Lima <renato.lima@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResCity(models.Model):
    _inherit = "res.city"
    _nfe_search_keys = ["ibge_code"]

    # nfe40_cMun = fields.Char(related="ibge_code", readonly=True)
    # nfe40_xMun = fields.Char(related="name", readonly=True)
    # nfe40_UF = fields.Char(related="state_id.code")
    # nfe40_cPais = fields.Char(related="country_id.bc_code")
    # nfe40_xPais = fields.Char(related="country_id.name")


