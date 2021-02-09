# Copyright 2017 KMEE INFORMATICA LTDA
#   Luiz Felipe do Divino <luiz.divino@kmee.com.br>
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    codigo_administradora_cartao = fields.Char(
        string="Código da Administradora",
    )

    eh_administradora_cartao = fields.Boolean(
        string="É Administradora de Cartão?"
    )
