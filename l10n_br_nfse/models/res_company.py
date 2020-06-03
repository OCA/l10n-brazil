# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

PROCESSADOR = 'erpbrasil_edoc'


class ResCompany(models.Model):

    _inherit = 'res.company'
    processador_edoc = fields.Selection(
        selection_add=[(PROCESSADOR, 'erpbrasil.edoc')]
    )
    provedor_nfse = fields.Selection(
        selection=[
            ('ginfes', 'Ginfes'),
            ('dsf', 'DSF / Iss Digital'),
        ],
        default='ginfes',
    )
    cultural_encourager = fields.Boolean(
        string='Cultural Encourager',
        default=False,
    )
