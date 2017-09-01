# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia -
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    sped_participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Participante',
        related='partner_id.sped_participante_id',
    )
    sped_empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        related='partner_id.sped_empresa_id',
    )
    is_brazilian = fields.Boolean(
        string='Is a Brazilian company?',
        related='partner_id.sped_participante_id.is_brazilian',
        store=True,
    )
