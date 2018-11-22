# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
import pandas as pd
import datetime
import calendar
import string
import random

def pega_periodos():
    periodo_list = []
    hj = datetime.datetime.now()

    for y in range(int(hj.year)-1, int(hj.year)+1):
        for m in range(1, 13):
            periodo_list.append(
                (str(m).zfill(2)+'.'+str(y), str(m).zfill(2)+'/'+str(y))
            )

    return periodo_list


class AccountFechamento(models.Model):
    _name = 'account.fechamento'
    _description = 'Modelo para criar os lançamentos de fechamento de períodos'
    _order = 'name'

    name = fields.Char(
        string=u'Nome',
    )

    periodo_ini = fields.Selection(
        selection=pega_periodos(),
        string=u'Periodo - Início',
    )

    periodo_fim = fields.Selection(
        selection=pega_periodos(),
        string=u'Periodo - Fim',
    )

    account_period_ids = fields.Many2many(
        string=u'Períodos',
        comodel_name='account.period',
    )

    fiscalyear_id = fields.Many2one(
        comodel_name='account.fiscalyear',
        string='Ano base',
    )

    account_move_ids = fields.One2many(
        string=u'Lançamentos Contábeis',
        comodel_name='account.move',
        inverse_name='account_fechamento_id',
        domain=[('lancamento_de_fechamento', '=', False)],
    )

    account_move_fechamento_ids = fields.One2many(
        string=u'Lançamentos Contábeis de Fechamento',
        comodel_name='account.move',
        inverse_name='account_fechamento_id',
        domain=[('lancamento_de_fechamento', '=', True)],
    )

    account_journal_id = fields.Many2one(
        string=u'Diário de fechamento',
        comodel_name='account.journal',
    )

    state = fields.Selection(
        selection=[
            ('open', 'Open'),
            ('close', 'Closed'),
        ],
        string='State',
        default='open',
    )

    @api.multi
    def button_fechar_periodos(self):
        """

        :return:
        """
        for record in self:
            record.state = 'close'

    @api.multi
    def button_buscar_lancamentos_do_periodo(self):
        """
        :return:
        """
        for record in self:

            for account_move_id in record.account_move_ids:
                account_move_id.account_fechamento_id = False

            dt_ini = str(record.periodo_ini.split('.')[1]) + '-'
            dt_ini += str(record.periodo_ini.split('.')[0]).zfill(2) + '-'
            dt_ini += '01'

            dt_fim = record.periodo_fim.split('.')[1] + '-'
            dt_fim += record.periodo_fim.split('.')[0].zfill(2) + '-'
            dt_fim += str(calendar.monthrange(
                int(record.periodo_fim.split('.')[1]),
                int(record.periodo_fim.split('.')[0]))[-1])

            account_move_ids = self.env['account.move'].search(
                [('period_id.date_start', '>=', dt_ini),
                 ('period_id.date_stop', '<=', dt_fim),
                 ('state', '=', 'posted'),
                 ('account_fechamento_id', '=', False),
                 ('journal_id.type','=','situation')])

            # Relacionar os lancamentos ao fechamento atual
            for account_move_id in account_move_ids:
                account_move_id.account_fechamento_id = record.id

    @api.multi
    def button_fechar_periodos(self):
        for record in self:
            # Cria dataframe vazio com colunas
            df_are = pd.DataFrame(
                columns=['conta', 'debito', 'credito', 'periodo', 'dt_stop'])

            # Popula o dataframe com valores do account.move.line
            for move in record.account_move_ids:
                for line in move.line_id:
                    df_are.loc[line.id] = [line.account_id.id, line.debit,
                                           line.credit, move.period_id.id,
                                           move.period_id.date_stop]

            data_lancamento = df_are['dt_stop'].max()
            periodo_id = df_are[
                data_lancamento == df_are['dt_stop']].iloc[1]['periodo']

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
                            'debit':  0.0,
                            'credit': abs(series_conta['result']),
                            'name': ''.join(
                                random.choice(string.uppercase) for x in
                                range(8))
                        }

                    record.env['account.move'].create({
                        'journal_id': record.account_journal_id.id,
                        'period_id': periodo_id,
                        'date': data_lancamento,
                        'state': 'posted',
                        'line_id':[(0, 0, conta_id), (0, 0, are_id)]
                    })

            record.state = 'close'
