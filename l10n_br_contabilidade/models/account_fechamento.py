# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import random
import string

import pandas as pd
from openerp import api, fields, models
from openerp.exceptions import Warning as UserError


class AccountFechamento(models.Model):
    _name = 'account.fechamento'
    _description = 'Modelo para criar os lançamentos de fechamento de períodos'
    _order = 'name'

    name = fields.Char(
        string=u'Nome',
    )

    periodo_ini = fields.Many2one(
        comodel_name='account.period',
        string=u'Periodo - Início',
    )

    periodo_fim = fields.Many2one(
        comodel_name='account.period',
        string=u'Periodo - Fim',
    )

    account_period_ids = fields.Many2many(
        string=u'Períodos',
        comodel_name='account.period',
    )

    fiscalyear_id = fields.Many2one(
        comodel_name='account.fiscalyear',
        string='Ano base',
        default=lambda self: self._get_defaults(),
    )

    account_move_ids = fields.One2many(
        string=u'Lançamentos Contábeis',
        comodel_name='account.move',
        inverse_name='account_fechamento_id',
        domain=[('lancamento_de_fechamento', '=', False)],
    )

    account_move_fechamento_ids = fields.One2many(
        string=u'Lançamentos Contábeis do Fechamento',
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

    def _get_defaults(self):
        fiscalyear_id = self.env['account.fiscalyear'].find()
        return fiscalyear_id

    @api.multi
    def button_fechar_periodos(self):
        """
        """
        for record in self:
            record.state = 'close'

    @api.multi
    def button_buscar_lancamentos_do_periodo(self):
        """
        :return:
        """
        for record in self:

            # Desfazer relacionamentos com os outros lançamentos
            record.account_move_ids = False

            # Buscar partidas em que as contas estão configuradas para tipo
            # resultado
            account_move_line_ids = self.env['account.move.line'].search([
                ('period_id.date_start', '>=', record.periodo_ini.date_start),
                ('period_id.date_stop', '<=', record.periodo_fim.date_stop),
                ('move_id.state', '=', 'posted'),
                ('move_id.account_fechamento_id', '=', False),
                ('account_id.user_type.report_type','in',['income', 'expense']),
            ])

            if not account_move_line_ids:
                raise UserError(
                    'Não foi encontrado lançamentos no período '
                    'para realizar o fechamento!'
                )

            # Buscar todos periodos do intervalo
            period_ids = self.periodo_ini.search([
                ('date_start','>=', record.periodo_ini.date_start),
                ('date_stop','<=', record.periodo_fim.date_stop),
            ])

            # Validar para Não encontrar períodos fechados no intervalo
            peridos_fechados = period_ids.filtered(lambda x: x.state == 'done')
            if peridos_fechados:
                raise UserError(
                    u'Períodos já encerrados no intervalo selecionado!')

            # Relacionar os lancamentos ao fechamento atual
            for account_move_id in account_move_line_ids.mapped('move_id'):
                account_move_id.account_fechamento_id = record.id

    @api.multi
    def button_reopen(self):
        for record in self:
            for move in record.mapped('account_move_fechamento_ids'):
                move.state = 'draft'

            record.account_move_fechamento_ids.unlink()

            for move in record.mapped('account_move_ids'):
                move.lancamento_de_fechamento = False

            record.account_move_ids = False
            record.state = 'open'

    @api.multi
    def button_fechar_periodos(self):
        for record in self:
            # Cria dataframe vazio com colunas
            df_are = pd.DataFrame(
                columns=['conta', 'debito', 'credito', 'periodo', 'dt_stop'])

            # Popula o dataframe com valores do account.move.line
            for move in record.account_move_ids:

                # Busca contas de resultado
                move_line = move.line_id.filtered(
                    lambda x: x.account_id.user_type.report_type
                              in ('income', 'expense'))

                if len(move_line) != 0:
                    raise UserError(
                        u'Não encontrada nenhuma conta de resultado'
                    )

                for line in move_line:
                    df_are.loc[line.id] = [line.account_id.id, line.debit,
                                           line.credit, move.period_id.id,
                                           move.period_id.date_stop]

            data_lancamento = df_are['dt_stop'].max()
            periodo_id = df_are[
                data_lancamento == df_are['dt_stop']].iloc[0]['periodo']

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
                        'account_fechamento_id': record.id,
                        'lancamento_de_fechamento': True,
                        'line_id':[(0, 0, conta_id), (0, 0, are_id)]
                    })

            record.state = 'close'
