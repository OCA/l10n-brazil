# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import random
import string

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

    account_period_ids = fields.One2many(
        string=u'Períodos',
        comodel_name='account.period',
        inverse_name='account_fechamento_id',
    )

    fiscalyear_id = fields.Many2one(
        comodel_name='account.fiscalyear',
        string='Ano base',
        default=lambda self: self._get_default_fiscalyear(),
    )

    account_journal_id = fields.Many2one(
        string=u'Diário de fechamento',
        comodel_name='account.journal',
        default=lambda self: self._get_default_journal(),
    )

    account_move_ids = fields.One2many(
        string='Lançamentos de Fechamento',
        comodel_name='account.move',
        inverse_name='account_fechamento_id',
    )

    state = fields.Selection(
        selection=[
            ('open', 'Aberto'),
            ('close', 'Fechado'),
        ],
        string='State',
        default='open',
    )

    # @api.onchange('fiscalyear_id')
    # def _on_change_fiscalyear_id(self):
    #     self.periodo_ini = self.fiscalyear_id.period_ids.filtered(
    #     lambda x: x.name == '01/'+self.fiscalyear_id.name)
    #     self.periodo_fim = self.fiscalyear_id.period_ids.filtered(
    #     lambda x: x.name == '12/'+self.fiscalyear_id.name)

    def _get_default_fiscalyear(self):
        fiscalyear_id = self.env['account.fiscalyear'].find()
        return fiscalyear_id

    def _get_default_journal(self):
        account_journal_id = self.env['account.journal'].search([
            ('type','=','situation')
        ], limit=1)
        return account_journal_id

    def _verifica_apuracao_resultado(self, lines):
        '''
        Verifica se o resultado foi positivo ou negativo.
        Se positivo, cria lançamento rateado entre as contas definidas no diário (divisao_resultado_ids)

        :return:
        '''
        for record in self:
            resultado = 0
            # "lines" recebe um generator vindo do método "fechar_periodo" em "account.period"
            # O último item do generator é uma lista contendo o ID do último período e a data do ultimo dia
            for line in lines:
                try:
                    resultado += line
                except:
                    dados_periodo = line

            line_list = []
            # Resultado for positivo -> rateia os valores de acordo com as porcentagens informadas por ordem de conta
            if resultado > 0:
                # Valores únicos da sequência ordenados
                for seq in set([c.sequencia for c in record.account_journal_id.divisao_resultado_ids]):
                    # Credito total da sequência
                    credito_total = 0

                    for conta in record.account_journal_id.divisao_resultado_ids.filtered(lambda s: s.sequencia == seq):
                        # Porcentagem/Valor Fixo do item em cima do total restante do resultado
                        credito = (conta.porcentagem/100)*resultado if conta.porcentagem != 0.0 else conta.valor_fixo
                        credito_total += credito

                        # Partida
                        line_list.append((0, 0, {
                            'account_id': conta.account_id.id,
                            'debit': 0.0,
                            'credit': credito,
                            'name': ''.join(random.choice(string.uppercase) for x in range(8))
                        }))

                    resultado = resultado - credito_total

                # Cria lançamento
                record.env['account.move'].create({
                    'journal_id': record.account_journal_id.id,
                    'period_id': dados_periodo[1],
                    'date': dados_periodo[0],
                    'state': 'posted',
                    'lancamento_de_fechamento': True,
                    'line_id': line_list
                })

    @api.multi
    def button_buscar_periodos(self):
        """
        :return:
        """
        for record in self:
            # Buscar todos periodos no intervalo indicado
            period_ids = self.env['account.period'].search([
                ('date_start', '>=', record.periodo_ini.date_start),
                ('date_stop', '<=', record.periodo_fim.date_stop),
                ('special', '!=', True),
            ])

            # Validar para Não encontrar períodos fechados no intervalo
            peridos_fechados = period_ids.filtered(lambda x: x.state == 'done')
            if peridos_fechados:
                raise UserError(u'Períodos já encerrados no intervalo selecionado!')

            # Associa o periodo a este fechamento
            record.account_period_ids = period_ids

    @api.multi
    def button_fechar_periodos(self):
        for record in self:
            record.button_buscar_periodos()
            for period_id in record.account_period_ids:
                period_id.account_journal_id = record.account_journal_id
                period_id.fechar_periodo(record)
            # Fecha período
            record.state = 'close'
            self._verifica_apuracao_resultado(period_id.fechar_periodo())

    @api.multi
    def button_reopen(self):
        for record in self:
            for period_id in record.mapped('account_period_ids'):
                period_id.reopen_period()

            record.account_period_ids = False
            record.state = 'open'
