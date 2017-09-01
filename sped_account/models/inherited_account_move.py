# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from openerp.addons.l10n_br_base.models.sped_base import SpedBase


class AccountMove(SpedBase, models.Model):
    _inherit = 'account.move'

    is_brazilian = fields.Boolean(
        string=u'Is a Brazilian Move?',
        compute='_compute_is_brazilian',
        store=True,
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        related='journal_id.empresa_id',
        store=True,
        readonly=True,
        default=lambda self: self.env.user.company_id.empresa_id,
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Participante',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        compute='_onchange_participante_id',
    )
    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string='Documento Fiscal',
        ondelete='restrict',
    )

    @api.depends('journal_id', 'company_id', 'currency_id', 'empresa_id')
    def _compute_is_brazilian(self):
        for move in self:
            if move.documento_id:
                move.is_brazilian = True
            elif move.empresa_id:
                move.is_brazilian = True

            if move.is_brazilian:
                #
                # Brazilian moves, by law, must always be in BRL
                #
                move.currency_id = self.env.ref('base.BRL').id
                continue

            move.is_brazilian = False

    @api.depends('participante_id')
    def _onchange_participante_id(self):
        self.ensure_one()
        self.partner_id = self.participante_id.partner_id

    @api.onchange('empresa_id')
    def _onchange_empresa_id(self):
        self.ensure_one()
        self.company_id = self.empresa_id.company_id

    @api.model
    def create(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(SaleOrder, self).create(dados)

    def write(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(SaleOrder, self).write(dados)
