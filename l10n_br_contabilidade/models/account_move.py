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

    state = fields.Selection(
        selection_add=[('cancel', u'Cancelado')]
    )

    lancamento_de_fechamento = fields.Boolean(
        string=u'Lançamento de Fechamento?',
        help='Indica se é um lançamento gerado apartir do fechamento',
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
        for line in self.line_id:
            line.state = 'cancel'
            line.situacao_lancamento = 'cancel'

    @api.multi
    def button_return(self):
        self.state = 'draft'
        for line in self.line_id:
            line.state = 'draft'
            line.situacao_lancamento = 'draft'

    @api.multi
    def validar_partidas_lancamento_contabil(self):
        """
        :return:
        """
        for record in self:
            if record and not record.line_id:
                raise Warning(
                    'Não é possível gerar um lançamento contábil sem partidas!')

    @api.model
    def create(self, vals):
        fiscalyear_id = \
            self.env['account.period'].browse(vals['period_id']).fiscalyear_id

        if not fiscalyear_id.sequence_id.id:
            fiscalyear_id.sequence_id = self.env['ir.sequence'].create({
                'name': 'account_move_sequence_' + fiscalyear_id.name,
                'implementation': 'no_gap'
            }).id

        vals['sequencia'] = \
            self.env['ir.sequence'].next_by_id(fiscalyear_id.sequence_id.id)

        res = super(AccountMove, self).create(vals)

        res.validar_partidas_lancamento_contabil()

        return res

    @api.onchange('journal_id', 'narration')
    def onchange_journal_id(self):
        """
        :param journal_id:
        :return:
        """
        for record in self:
            if record.journal_id:

                historico_padrao = \
                    record.journal_id.template_historico_padrao_id.get_historico_padrao()

                if historico_padrao:
                    record.name = historico_padrao

                if record.name and record.narration:
                    record.resumo = str(record.name + ' ' + record.narration)[:250]

    @api.model
    def write(self, vals):
        for record in self:

            # Quando lançamento ja estiver lançado validar a alteração
            if record.state == 'posted':

                # Campos permitidos
                campos_permitidos = ['state', 'account_fechamento_id',
                                     'lancamento_de_fechamento']

                # Alteração apenas dos campos permitidos
                # Removo os campos permitidos do conjunto de campos a alterar
                if set(vals.keys()) - set(campos_permitidos):
                    raise Warning(
                        u'Não é possível editar um lançamento com '
                        u'status lançado.')

        res = super(AccountMove, self).write(vals)

        self.validar_partidas_lancamento_contabil()

        return res

    @api.multi
    def post(self):
        res = super(AccountMove, self).post()

        for line in self.line_id:
            line.situacao_lancamento = 'posted'

        return res
