# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import random
import string

from dateutil.relativedelta import relativedelta
from openerp import api, fields, models
from openerp.exceptions import Warning as UserError


class AccountPeriod(models.Model):
    _inherit = 'account.period'

    account_move_ids = fields.One2many(
        string=u'Lançamentos Contábeis',
        comodel_name='account.move',
        inverse_name='period_id',
        domain=[('lancamento_de_fechamento', '=', False)],
    )

    account_move_fechamento_ids = fields.One2many(
        string=u'Lançamentos Contábeis do Fechamento',
        comodel_name='account.move',
        inverse_name='period_id',
        domain=[('lancamento_de_fechamento', '=', True)],
    )

    account_fechamento_id = fields.Many2one(
        string=u'Fechamento',
        comodel_name='account.fechamento',
    )

    account_journal_id = fields.Many2one(
        string=u'Diário de fechamento',
        comodel_name='account.journal',
    )

    account_saldo_ids = fields.One2many(
        comodel_name='account.saldo',
        string='Saldo do Período',
        inverse_name='account_period_id',
    )

    detalhar_contas_superiores = fields.Boolean(
        string='Exibir Contas superiores',
    )

    exibir_conta_raiz = fields.Boolean(
        string='Exibir Conta Raiz',
        default=True,
    )

    demonstracao_periodo_atual = fields.Boolean(
        string='Apuração somente do período Atual?',
        default=True,
        help='Apurar as demonstrações somente com lançamentos do período '
             'corrente. Caso não esteja marcado utilizará os lançamentos a '
             'partir do ultimo período finalizado.',
    )

    demonstracao_start_periodo = fields.Many2one(
        string='Período Inicial',
        comodel_name='account.period',
        help='Caso opte pelas demonstrações iniciarem a partir do ultimo '
             'período fechado, esse campo indicará o período que se iniciará '
             'a busca por lançamentos',
        default=lambda self: self.default_demonstracao_start_periodo(),
    )

    account_account_report_line_ids = fields.One2many(
        comodel_name='account.account.report.line',
        string='Contas de Apresentação',
        inverse_name='period_id',
    )

    @api.multi
    def button_fechar_periodo(self):
        for record in self:
            record.fechar_periodo()

    @api.multi
    def fechar_periodo(self):
        """

        :return:
        """
        for record in self:
            # Altera estado
            record.state = 'done'

    @api.multi
    def reopen_period(self):
        """
        :return:
        """
        for record in self:
            for move in record.account_move_fechamento_ids:
                move.state = 'draft'

            record.account_move_fechamento_ids.unlink()

            for move in record.account_move_ids:
                move.lancamento_de_fechamento = False

            record.state = 'draft'

    @api.onchange('demonstracao_periodo_atual')
    def onchange_demonstracao_periodo_atual(self):
        """
        :return:
        """
        for record in self:
            if record.demonstracao_periodo_atual:
                record.demonstracao_start_periodo = False

            else:
                record.demonstracao_start_periodo = \
                    self.default_demonstracao_start_periodo()

    def get_periodo_anterior(self, period_id=False):
        """
        Buscar o periodo anterior a partir do periodo do parametro
        :return: account.period
        """

        if self and not period_id:
            period_id = self
        date_start_periodo_anterior = \
            fields.Date.from_string(
                period_id.date_start or fields.Date.today()) - relativedelta(
                months=1)
        return self.search([
            ('date_start', '=', str(date_start_periodo_anterior))], limit=1)

    def get_periodo_seguinte(self, period_id=False):
        """
        :return:
        """
        if self and not period_id:
            period_id = self
        date_start_periodo_atual = \
            fields.Date.from_string(
                period_id.date_start or fields.Date.today()) + \
            relativedelta(months=1)
        return self.search([
            ('date_start', '=', str(date_start_periodo_atual))], limit=1)

    def get_ultimo_periodo_fechado(self):
        """
        :return:
        """
        last_closed_period = self.search([
            ('state', '=', 'done'),
        ], order='date_start DESC', limit=1)

        return last_closed_period

    def default_demonstracao_start_periodo(self):
        """
        :return:
        """
        return self.get_periodo_seguinte(self.get_ultimo_periodo_fechado())

    def get_saldo_inicial_conta(self, account_id):
        """
        Definir o saldo inicial da conta no período
        :return: float
        """
        saldo_id = self.env['account.saldo'].search([
            ('account_period_id', '=', self.get_periodo_anterior().id),
            ('account_account_id', '=', account_id.id),
        ])
        return saldo_id.saldo_final or 0.00

    def get_parent_account(self, contas_ids):
        """
        :param contas_ids:
        :return:
        """
        # Configuracao para exibir a conta 0
        if not self.exibir_conta_raiz and \
                contas_ids.user_type.name == 'Raiz/Visão':
            return self.env['account.account']

        all_contas = contas_ids
        for conta_id in contas_ids:
            if conta_id.parent_id:
                all_contas += self.get_parent_account(conta_id.parent_id)
            return all_contas

    def gerar_saldos_periodo(self, account_id, saldo_inicial,
                             debit, credit, result_period, result):
        """
        Baseado na movimentação da conta, gerar saldos para o balancete do
        periodo selecionado
        """
        if self.detalhar_contas_superiores:
            account_id = self.get_parent_account(account_id)

        for conta_id in account_id:
            if result:
                self.env['account.saldo'].create({
                    'name': conta_id.display_name,
                    'account_account_id': conta_id.id,
                    'account_period_id': self.id,
                    'saldo_inicial': saldo_inicial,
                    'debito_periodo': debit,
                    'credito_periodo': credit,
                    'saldo_periodo': result_period,
                    'saldo_final': result,
                })

    def get_partidas_periodo(self, period_id_inicial, period_final):
        """
        :return:
        """
        partidas_ids = self.env['account.move.line'].search([
            ('date', '>=', period_id_inicial.date_start),
            ('date', '<=', period_final.date_stop),
            ('move_id.state', '=', 'posted'),
            ('account_id.user_type.report_type', 'in', ('income', 'expense')),
        ])
        return partidas_ids

    @api.multi
    def gerar_balancete(self):
        """
        Gerar registro de saldos das contas dentro de um período
        :return:
        """

        for record in self:
            # Excluir saldos antigos
            record.account_saldo_ids.unlink()

            # Contas alteradas no período
            if record.demonstracao_periodo_atual:
                # Contas para gerar saldo. Definir contas para agrupar partidas
                contas_ids = record.account_move_ids.mapped('line_id') \
                    .mapped('account_id')

            else:
                # Partidas desde o ultimo periodo finalizado
                partidas_periodo_ids = \
                    self.get_partidas_periodo(
                        record.demonstracao_start_periodo, record)

                contas_ids = partidas_periodo_ids.mapped('account_id')

            for conta_id in contas_ids:

                # Lançamentos do período
                if record.demonstracao_periodo_atual:
                    partidas = self.account_move_ids.mapped('line_id'). \
                        filtered(lambda x: x.account_id == conta_id)

                # Lançamentos apartir do ultimo fechado
                if not record.demonstracao_periodo_atual:
                    partidas = partidas_periodo_ids. \
                        filtered(lambda x: x.account_id == conta_id)

                # Saldo inicial da conta no período
                saldo_inicial = self.get_saldo_inicial_conta(conta_id)

                debit = sum(partidas.mapped('debit'))
                credit = sum(partidas.mapped('credit'))
                result_period = debit - credit
                result = saldo_inicial + result_period

                self.gerar_saldos_periodo(
                    conta_id, saldo_inicial, debit, credit,
                    result_period, result)

    @api.multi
    def gerar_dre_periodo(self):
        """
        :return:
        """
        for record in self:
            record.account_account_report_line_ids.unlink()

            account_reports = {}

            # Contas alteradas no período
            if record.demonstracao_periodo_atual:
                # Contas para gerar saldo. Definir contas para agrupar partidas
                account_move_line_ids = \
                    self.get_partidas_periodo(record, record)

            else:
                # Partidas desde o ultimo periodo finalizado
                account_move_line_ids = \
                    self.get_partidas_periodo(
                        record.demonstracao_start_periodo, record)

            self.env['account.account.report'].gerar_reports(
                record, account_move_line_ids)
