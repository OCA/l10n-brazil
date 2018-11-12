# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'
    _sql_constraints = [ ('unique_sequencia','unique(sequencia)',u'Número da sequência já existe.'), ]

    centro_custo_id = fields.Many2many(
        string='Centro de Custo',
        comodel_name='account.centro.custo',
    )

    sequencia = fields.Integer(
        string='Sequência',
        default=lambda self: self._get_default_sequence(),
        unique=True,
    )

    @api.multi
    def _get_default_sequence(self):
        ultimo_lancamento = self._get_last_sequence()
        proximo_numero = ultimo_lancamento.sequencia + 1

        return proximo_numero

    ramo_id = fields.Many2one(
        'account.ramo',
        string=u'Ramo',
    )

    def _get_last_sequence(self):
        return self.search(
            [('sequencia', '!=', False)], order='sequencia DESC', limit=1
        )

    @api.model
    def create(self, vals):
        if self._get_last_sequence().sequencia == vals['sequencia']:
            vals['sequencia'] = self._get_default_sequence()

        return super(AccountMove, self).create(vals)
