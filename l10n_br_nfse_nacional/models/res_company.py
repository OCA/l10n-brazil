# Copyright 2023 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    provedor_nfse = fields.Selection(
        selection_add=[
            ("nacional", "Padrão Nacional"),
        ]
    )
