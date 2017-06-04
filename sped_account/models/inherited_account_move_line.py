# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from ..constantes import NATUREZA_PARTIDA, NATUREZA_PARTIDA_DEBITO, \
    NATUREZA_PARTIDA_CREDITO


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_brazilian_move = fields.Boolean(
        string=u'Is a Brazilian Move?',
        related='move_id.is_brazilian_move',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='move_id.company_id',
        store=True,
        readonly=True,
    )
    sped_empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        related='move_id.sped_empresa_id',
        store=True,
        readonly=True,
    )
    sped_participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Participante',
        related='move_id.sped_participante_id',
        store=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        related='move_id.partner_id',
        store=True,
        readonly=True,
    )
    natureza = fields.Selection(
        selection=NATUREZA_PARTIDA,
        string='Natureza da partida',
        compute='_compute_natureza',
        store=True,
    )

    @api.depends('debit', 'credit')
    def _compute_natureza(self):
        for move_line in self:
            if move_line.debit != 0:
                move_line.natureza = NATUREZA_PARTIDA_DEBITO
            elif move_line.credit != 0:
                move_line.natureza = NATUREZA_PARTIDA_CREDITO
