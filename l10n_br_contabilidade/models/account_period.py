# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import random
import string

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

    @api.multi
    def fechar_periodo(self):
        """

        :return:
        """
        for record in self:
            # Cria dataframe vazio com colunas
            df_are = pd.DataFrame(columns=['conta', 'debito', 'credito', 'periodo', 'dt_stop'])

            # Popula o dataframe com valores do account.move.line
            for move in record.account_move_ids:

                # Busca contas de resultado
                partidas_resultado = move.line_id.filtered(
                    lambda x: x.account_id.user_type.report_type in ('income', 'expense'))

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
