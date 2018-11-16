# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import Warning

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

    state = fields.Selection(selection_add=[('cancel', u'Cancelado')])

    ramo_id = fields.Many2one(
        'account.ramo',
        string=u'Ramo',
    )

    historico_padrao_id = fields.Many2one(
        comodel_name='account.historico.padrao',
        string=u'Modelo do Histórico Padrão',
    )

    resumo = fields.Char(
        string=u'Resumo',
        size=250,
        compute='onchange_journal_id',
    )

    @api.multi
    def button_cancel(self):
        self.state = 'cancel'

    @api.multi
    def button_return(self):
        self.state = 'draft'

    @api.model
    def create(self, vals):
        fiscalyear_id = self.env['account.period'].browse(vals['period_id']).fiscalyear_id

        if not fiscalyear_id.sequence_id.id:
            fiscalyear_id.sequence_id = self.env['ir.sequence'].create(
                {'name': 'account_move_sequence_'+fiscalyear_id.name, 'implementation': 'no_gap'}).id

        vals['sequencia'] = self.env['ir.sequence'].next_by_id(fiscalyear_id.sequence_id.id)

        return super(AccountMove, self).create(vals)

    @api.onchange('journal_id', 'narration')
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

            if self.name and self.narration:
                self.resumo = str(self.name + ' ' + self.narration)[:250]

    @api.model
    def write(self, vals):
        for record in self:
            if record.state == 'posted' and not vals['state']:
                raise Warning(u'Não é possível editar um lançamento com status lançado.')

        return super(AccountMove, self).write(vals)
