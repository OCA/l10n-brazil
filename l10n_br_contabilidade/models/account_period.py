# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import random
import string
from dateutil.relativedelta import relativedelta

import pandas as pd
from openerp import api, fields, models


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
        related='account_fechamento_id.account_journal_id',
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

    @api.multi
    def fechar_periodo(self):
        """

        :return:
        """
        for record in self:
            # Cria dataframe vazio com colunas
            df_are = pd.DataFrame(
                columns=['conta', 'debito', 'credito', 'periodo', 'dt_stop'])

            # Popula o dataframe com valores do account.move.line
            for move in record.account_move_ids:

                # Busca contas de resultado
                partidas_resultado = move.line_id.filtered(
                    lambda x: x.account_id.user_type.report_type in
                              ('income', 'expense'))

                for partida_resultado in partidas_resultado:
                    df_are.loc[partida_resultado.id] = [
                        partida_resultado.account_id.id,
                        partida_resultado.debit,
                        partida_resultado.credit,
                        move.period_id.id,
                        move.period_id.date_stop
                    ]

            data_lancamento = df_are['dt_stop'].max()

            # Agrupa por conta e soma as outras colunas
            df_agrupado = df_are.groupby('conta').sum()
            df_agrupado['result'] = \
                (df_agrupado['debito'] - df_agrupado['credito'])

            # Conta de credito e debito ARE padrão
            are_debito = record.account_journal_id.default_debit_account_id.id
            are_credito = record.account_journal_id.default_credit_account_id.id

            for conta in df_agrupado.index:
                series_conta = df_agrupado.loc[conta]
                if series_conta['result'] != 0.0:
                    if series_conta['result'] > 0.0:
                        conta_id = {
                            'account_id': int(conta),
                            'debit': 0.0,
                            'credit': series_conta['result'],
                            'name': ''.join(
                                random.choice(string.uppercase) for x in
                                range(8))
                        }

                        are_id = {
                            'account_id': int(are_debito),
                            'debit': series_conta['result'],
                            'credit': 0.0,
                            'name': ''.join(
                                random.choice(string.uppercase) for x in
                                range(8))
                        }

                    elif series_conta['result'] < 0.0:
                        conta_id = {
                            'account_id': int(conta),
                            'debit': abs(series_conta['result']),
                            'credit': 0.0,
                            'name': ''.join(
                                random.choice(string.uppercase) for x in
                                range(8))
                        }

                        are_id = {
                            'account_id': int(are_credito),
                            'debit': 0.0,
                            'credit': abs(series_conta['result']),
                            'name': ''.join(
                                random.choice(string.uppercase) for x in
                                range(8))
                        }

                    record.env['account.move'].create({
                        'journal_id': record.account_journal_id.id,
                        'period_id': record.id,
                        'date': data_lancamento,
                        'state': 'posted',
                        'lancamento_de_fechamento': True,
                        'line_id': [(0, 0, conta_id), (0, 0, are_id)]
                    })

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


    def get_period_anterior(self):
        """
        Buscar o periodo anterior a partir do periodo instanciado
        :return: account.period
        """
        date_start_periodo_anterior = \
            fields.Date.from_string(self.date_start) - relativedelta(months=1)
        return self.search([
            ('date_start', '=', str(date_start_periodo_anterior))], limit=1)

    def get_saldo_inicial_conta(self, account_id):
        """
        Definir o saldo inicial da conta no período
        :return: float
        """
        saldo_id = self.env['account.saldo'].search([
            ('account_period_id', '=', self.get_period_anterior().id),
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

    @api.multi
    def gerar_balancete(self):
        """
        Gerar registro de saldos das contas dentro de um período
        :return:
        """

        for record in self:
            # Excluir saldos antigos
            record.account_saldo_ids.unlink()

            # Contas para gerar saldo. Gerar apenas de contas, que for
            # que lançamentos contábeis
            contas_ids = \
                record.account_move_ids.mapped('line_id').mapped('account_id')

            for conta_id in contas_ids:

                # Lançamentos dentro do período
                partidas = self.account_move_ids.mapped('line_id').\
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
