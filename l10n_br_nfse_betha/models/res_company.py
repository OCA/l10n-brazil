# Copyright (C) 2023-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    provedor_nfse = fields.Selection(
        selection_add=[
            ("betha", "Betha"),
        ]
    )
