# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    provedor_nfse = fields.Selection(
        selection_add=[
            ("giss", "GissOnline"),
        ]
    )
    nfse_giss_host = fields.Char(
        string="GissOnline Host",
        help="Prefix of the production host of the city "
        "(ws-<host>.giss.com.br), for a city the library does not know yet. "
        "Leave empty to use the host of the city of the company.",
    )
