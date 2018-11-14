# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    centro_custo_id = fields.Many2many(
        string='Centro de Custo',
        comodel_name='account.centro.custo',
    )

    sequencia = fields.Integer(
        string=u'Sequência',
        required=True,
    )

    ramo_id = fields.Many2one(
        'account.ramo',
        string=u'Ramo',
    )

    historico_padrao_id = fields.Many2one(
        comodel_name='account.historico.padrao',
        string=u'Modelo do Histórico Padrão',
    )

    @api.model
    def create(self, vals):
        year = self.env['account.period'].browse(vals['period_id']).fiscalyear_id.name
        sequence_id = self.env['ir.sequence'].search([('name','=','account_move_sequence_'+year)]).id
        sequence_id = sequence_id if sequence_id else self.env['ir.sequence'].create(
            {'name': 'account_move_sequence_'+year, 'implementation': 'no_gap'}).id
        vals['sequencia'] = self.env['ir.sequence'].next_by_id(sequence_id)

        return super(AccountMove, self).create(vals)

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        """
        :param journal_id:
        :return:
        """
        if self.journal_id:

            historico_padrao = \
                self.journal_id.template_historico_padrao_id.get_historico_padrao()

            if historico_padrao:
                self.name = historico_padrao
