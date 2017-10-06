# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import fields, models


class SpedParticipante(models.Model):
    _inherit = 'sped.participante'

    cnae_id = fields.Many2one(
        comodel_name='sped.cnae',
        string='CNAE principal'
    )
    operacao_produto_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação padrão para venda',
        ondelete='restrict',
        domain=[('modelo', 'in', ('55', '65', '2D')), ('emissao', '=', '0')],
    )
    operacao_servico_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação padrão para venda',
        ondelete='restrict',
        domain=[('modelo', 'in', ('SE', 'RL')), ('emissao', '=', '0')],
    )
