# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_brazilian_move = fields.Boolean(
        string=u'Is a Brazilian Move?',
        compute='_compute_is_brazilian_move',
        store=True,
    )
    sped_empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        related='journal_id.sped_empresa_id',
        store=True,
        readonly=True,
        default=lambda self: self.env.user.company_id.sped_empresa_id,
    )
    sped_participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Participante',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        compute='_onchange_sped_participante_id',
    )

    @api.depends('journal_id', 'company_id', 'currency_id', 'sped_empresa_id')
    def _compute_is_brazilian_move(self):
        for move in self:
            if move.company_id.country_id:
                if move.sped_empresa_id:
                    move.is_brazilian_move = True

                    #
                    # Brazilian moves, by law, must always be in BRL
                    #
                    move.currency_id = self.env.ref('base.BRL').id

                    continue

            move.is_brazilian_move = False

    @api.depends('sped_participante_id')
    def _onchange_sped_participante_id(self):
        for move in self:
            if move.sped_participante_id:
                move.partner_id = move.sped_participante_id.partner_id
            else:
                move.partner_id = False
