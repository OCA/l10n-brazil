# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import Warning
from openerp import SUPERUSER_ID


class AccountMove(models.Model):
    _inherit = 'account.move'

    centro_custo_id = fields.Many2many(
        string='Centro de Custo',
        comodel_name='account.centro.custo',
    )

    sequencia = fields.Integer(
        string=u'Sequência',
    )

    account_invoice_id = fields.Many2one(
        string='Nota Fiscal',
        comodel_name='account.invoice',
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Unposted'),
            ('validacao_criacao', u'Validar Criação'),
            ('posted', 'Posted'),
            ('cancel', u'Cancelado')
        ],
    )

    lancamento_de_fechamento = fields.Boolean(
        string=u'Lançamento de Fechamento?',
        help='Indica se é um lançamento gerado apartir do fechamento',
    )

    account_fechamento_id = fields.Many2one(
        comodel_name='account.fechamento',
        string='Fechamnto relacionado',
    )

    account_event_id = fields.Many2one(
        string='Evento Contábil',
        comodel_name='account.event',
    )

    historico_padrao_id = fields.Many2one(
        comodel_name='account.historico.padrao',
        string=u'Modelo do Histórico Padrão',
    )

    resumo = fields.Char(
        string=u'Resumo',
        size=250,
        compute='compute_resumo',
    )

    criado_por = fields.Many2one(
        string='Criado Por',
        comodel_name='hr.employee',
    )

    criado_data = fields.Date(
        string='Criado Em',
    )

    editado_por = fields.Many2one(
        string=u'Última Edição Por',
        comodel_name='hr.employee',
    )

    editado_data = fields.Date(
        string=u'Última Edição Em',
    )

    validado_por = fields.Many2one(
        string='Validado Por',
        comodel_name='hr.employee',
    )

    validado_data = fields.Date(
        string='Validado Em',
    )

    fiscalyear_id = fields.Many2one(
        string='Ano Fiscal',
        comodel_name='account.fiscalyear',
        related='period_id.fiscalyear_id',
        store=True,
    )

    account_event_line_ids = fields.One2many(
        string='Linhas de eventos contábeis',
        comodel_name='account.event.line',
        inverse_name='account_move_id',
    )

    @api.multi
    def button_cancel(self):
        for record in self:
            self.state = 'cancel'
            for line in self.line_id:
                line.state = 'cancel'
                line.situacao_lancamento = 'cancel'

    @api.multi
    def button_return(self):
        for record in self:
            record.retornar_rascunho()

    def retornar_rascunho(self):
        self.state = 'draft'
        for line in self.line_id:
            line.state = 'draft'
            line.situacao_lancamento = 'draft'
        self.validado_por = False
        self.validado_data = False

    @api.multi
    def verifica_status_periodo(self):
        """
        :return:
        """
        for record in self:
            if record.lancamento_de_fechamento:
                return True

            if record.period_id.state == 'done':
                raise Warning(u'Período escolhido para '
                              u'este lançamento esta fechado!')

    @api.onchange('date')
    def onchange_date(self):
        """
        Definir o periodo de acordo com a data inputada
        """
        for record in self:
            record.period_id = record.period_id.find(record.date)

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
        res = super(AccountMove, self).create(vals)

        res.validar_partidas_lancamento_contabil()

        res.criado_por = self.env.user.employee_ids.id
        res.criado_data = fields.Date.today()

        return res

    @api.depends('journal_id', 'narration')
    def compute_resumo(self):
        """
        :param journal_id:
        :return:
        """
        for record in self:
            if record.journal_id:
                if not record.narration:
                    historico_padrao = record.journal_id. \
                        template_historico_padrao_id.get_historico_padrao()
                    record.narration = historico_padrao

                record.resumo = record.narration
                record.name = record.resumo
                record.ref = record.journal_id.ref

    @api.model
    def write(self, vals):
        for record in self:

            # Quando lançamento ja estiver lançado validar a alteração
            if record.state == 'posted':

                # Campos permitidos
                campos_permitidos = ['state', 'account_fechamento_id',
                                     'lancamento_de_fechamento', 'criado_por',
                                     'criado_data', 'editado_por',
                                     'editado_data', 'validado_por',
                                     'validado_data', 'narration']

                # Alteração apenas dos campos permitidos
                # Removo os campos permitidos do conjunto de campos a alterar
                if set(vals.keys()) - set(campos_permitidos):
                    raise Warning(
                        u'Não é possível editar um lançamento com '
                        u'status lançado.')

            if vals.get('state') == 'posted':
                self.verifica_status_periodo()

        if not vals.get('validado_por'):
            vals['editado_por'] = self.env.user.employee_ids.id
            vals['editado_data'] = fields.Date.today()

        res = super(AccountMove, self).write(vals)

        self.validar_partidas_lancamento_contabil()

        return res

    def verificar_employee_validacao(self):
        employee_id = self.env.user.employee_ids.id
        superuser = self.env.user.id == SUPERUSER_ID

        if not superuser and self.criado_por.id and employee_id == self.criado_por.id:
            raise Warning(
                'O empregado que criou o lançamento não pode '
                'validar este mesmo lançamento!'
            )

    @api.multi
    def post(self):
        self.verificar_employee_validacao()

        self.validado_por = self.env.user.employee_ids.id
        self.validado_data = fields.Date.today()

        if not self.sequencia:
            fiscalyear_id = \
                self.env['account.period'].find(self.date).fiscalyear_id

            if not fiscalyear_id.sequence_id.id:
                fiscalyear_id.sequence_id = self.env['ir.sequence'].create({
                    'name': 'account_move_sequence_' + fiscalyear_id.name,
                    'implementation': 'no_gap'
                }).id
                self.env.cr.commit()

            self.sequencia = self.env['ir.sequence'].next_by_id(
                fiscalyear_id.sequence_id.id)

        res = super(AccountMove, self).post()

        self.verifica_status_periodo()

        for line in self.line_id:
            line.situacao_lancamento = 'posted'

        return res

    @api.multi
    def button_validar_criacao(self):
        for record in self:
            record.state = 'validacao_criacao'

    @api.multi
    def atualizar_historico_lancamento(self):
        self.ensure_one()

        if self.journal_id.template_historico_padrao_id:
            historico_padrao = self.journal_id.template_historico_padrao_id.\
                get_historico_padrao()
            for line in self.mapped('line_id'):
                line.atualizar_nome(historico_padrao=historico_padrao)

        else:
            raise Warning(u'Necessário definir um Template Padrão do '
                          u'Lançamento para atualização dos históricos '
                          u'padrões')

    @api.multi
    def reverter_lancamento(self, account_event_reversao_id=False,
                            data=fields.Date.today()):
        """
        :param account_event_reversao_id:
        :param data:
        :return:
        """
        for record in self:
            account_move_line_obj = self.env['account.move.line']

            description = 'Reversão do Lançamento: {}/{} - {}'.format(
                record.sequencia,
                record.fiscalyear_id.name, record.resumo)

            period_id = self.env['account.period'].find(data)

            account_move_reversao = record.copy({
                'name': description,
                'narration': description,
                'date': data,
                'period_id': period_id.id,
                'sequencia': False,
                'validado_por': False,
                'validado_data': False,
            })

            if account_event_reversao_id:
                account_move_reversao['account_event_id'] = \
                    account_event_reversao_id.id

            lines_remocao = account_move_reversao.line_id.ids

            for line_id in record.line_id:
                account_move_line_obj.create({
                    'account_id': line_id.account_id.id,
                    'debit': line_id.credit,
                    'credit': line_id.debit,
                    'move_id': account_move_reversao.id,
                    'name': description,
                })

            for line in account_move_reversao.line_id:
                if line.id in lines_remocao:
                    line.unlink()

    @api.multi
    def button_reverter_lancamento(self):
        for record in self:
            record.reverter_lancamento()
