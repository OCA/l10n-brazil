# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ResCompany(models.Model):

    _inherit = 'res.company'

    provedor_nfse = fields.Selection(
        selection_add=[
            ('ginfes', 'Ginfes'),
        ]
    )
