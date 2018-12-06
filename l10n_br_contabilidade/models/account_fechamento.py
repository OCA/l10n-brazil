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

    account_move_reclassificacao_id = fields.Many2one(
        string=u'Lançamentos da Reclassificação',
        comodel_name='account.move',
    )

    account_move_distribuicao_id = fields.Many2one(
        string=u'Lançamentos da Distribuição',
        comodel_name='account.move',
    )


    state = fields.Selection(
        selection=[
            ('open', 'Aberto'),
            ('close', 'Fechado'),
            ('investigated', 'Apurado'),
            ('reclassified', 'Reclassificado'),
            ('distributed', 'Distribuído'),
        ],
        string='State',
        default='open',
    )

    def _get_default_fiscalyear(self):
        fiscalyear_id = self.env['account.fiscalyear'].find()
        return fiscalyear_id

    def _get_default_journal(self):
        account_journal_id = self.env['account.journal'].search([
            ('type', '=', 'situation')
        ], limit=1)
        return account_journal_id

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
            record.state = 'close'
            record.button_buscar_periodos()
            for period_id in record.account_period_ids:
                period_id.account_journal_id = record.account_journal_id
                period_id.fechar_periodo()

    @api.multi
    def button_apurar_periodos(self):
        for record in self:
            record.state = 'investigated'
            for period_id in record.account_period_ids:
                period_id.apurar_periodo()

    @api.multi
    def gera_lancamento_partidas(self, move, lines):
        line_list = []
        for record in self:
            for line in lines:
                line_list.append((0, 0, {
                    'account_id': line.get('account_id'),
                    'debit': abs(line.get('debit')),
                    'credit': abs(line.get('credit')),
                    'name': ''.join(random.choice(string.uppercase) for x in range(8))
                }))

            return record.env['account.move'].create({
                    'journal_id': move.get('journal_id'),
                    'period_id': move.get('period_id'),
                    'date': move.get('date'),
                    'state': 'posted',
                    'line_id': line_list
                })

    @api.multi
    def conta_are(self, op):
        """

        :param op: D/C (Débito/Crédito)
        :return:
        """
        for record in self:
            return record.account_journal_id.default_credit_account_id if op == 'C' \
                else record.account_journal_id.default_debit_account_id

    @api.multi
    def conta_reclassificacao(self, op):
        """

        :param op: L/P (Lucro/Prejuízo)
        :return:
        """
        for record in self:
            return record.account_journal_id.account_lucro_id if op == 'L' \
                else record.account_journal_id.account_prejuizo_id

    @api.multi
    def button_reclassificacao(self):
        for record in self:
            credito_are = 0
            debito_are = 0

            # Soma valores debito/crédito ARE
            for move in record.account_move_ids:
                credito_are += move.line_id.filtered(lambda x: x.account_id == self.conta_are(op='C')).credit
                debito_are += move.line_id.filtered(lambda x: x.account_id == self.conta_are(op='D')).debit

            resultado = credito_are - debito_are

            line_list = []

            # Crédito > Debito = Lucro
            if resultado > 0:
                # Partida 1 -> Credita valor na conta Lucro
                line_list.append({
                    'account_id': self.conta_reclassificacao(op='L').id,
                    'debit': 0.0,
                    'credit': resultado,
                })

                # Partida 2 -> Debita valor da conta ARE
                line_list.append({
                    'account_id': self.conta_are(op='D').id,
                    'debit': resultado,
                    'credit': 0.0,
                })

            # Crédito < Debito = Prejuízo
            elif resultado < 0:
                # Partida 1 -> Debita valor na conta Prejuízo
                line_list.append({
                    'account_id': self.conta_reclassificacao(op='P').id,
                    'debit': resultado,
                    'credit': 0.0,
                })

                # Partida 2 -> Credita valor na conta ARE
                line_list.append({
                    'account_id': self.conta_are(op='C').id,
                    'debit': 0.0,
                    'credit': resultado,
                })

            # Lançamento
            move = {
                'journal_id': record.account_journal_id.id,
                'period_id': record.periodo_fim.id,
                'date': record.periodo_fim.date_stop,
            }

            # Associa lançamento ao encerramento
            record.account_move_reclassificacao_id = record.gera_lancamento_partidas(move=move, lines=line_list).id

            record.state = 'distributed' if record.account_move_reclassificacao_id else 'reclassified'

    @api.multi
    def button_distribuir_resultado(self):
        """

        :return:
        """
        for record in self:
            # Pega o valor resultado
            cred_reclass = record.account_move_reclassificacao_id.line_id.filtered(
                    lambda x: x.account_id == record.conta_reclassificacao(op='L'))

            line_list = []

            # Verifica se existe Lucro
            if cred_reclass:
                resultado = cred_reclass.credit

                for seq in set([c.sequencia for c in record.account_journal_id.divisao_resultado_ids]):
                    # Credito total da sequência
                    credito_total = 0

                    for conta in record.account_journal_id.divisao_resultado_ids.filtered(lambda s: s.sequencia == seq):
                        # Porcentagem/Valor Fixo do item em cima do total restante do resultado
                        credito = (conta.porcentagem/100)*resultado if conta.porcentagem != 0.0 else conta.valor_fixo
                        credito_total += credito

                        # Debita da conta de Reclassificação Crédito
                        line_list.append({
                            'account_id': cred_reclass.account_id.id,
                            'debit': credito,
                            'credit': 0.0,
                        })

                        # Credita na conta rateada
                        line_list.append({
                            'account_id': conta.account_id.id,
                            'debit': 0.0,
                            'credit': credito,
                        })

                    # Subtraí o valor creditado do Resultado restante
                    resultado = resultado - credito_total

                # Lançamento
                move = {
                    'journal_id': record.account_journal_id.id,
                    'period_id': record.periodo_fim.id,
                    'date': record.periodo_fim.date_stop,
                }

                # Cria Lançamento e Partidas
                record.account_move_reclassificacao_id = record.gera_lancamento_partidas(move=move, lines=line_list).id

                record.state = 'reclassified' if record.account_move_reclassificacao_id else 'investigated'


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
        """

        :return:
        """
        for record in self:
            record.button_buscar_periodos()
            record._validar_lancamentos_periodo()
            for period_id in record.account_period_ids:
                period_id.account_journal_id = record.account_journal_id
                period_id.fechar_periodo()
            # Fecha Encerramento (Altera o status)
            record.state = 'close'

    def _validar_lancamentos_periodo(self):
        """

        :return:
        """
        for period_id in self.account_period_ids:
            if period_id.account_move_ids:
                return True

        raise UserError(
            u'Não existem lançamentos nos períodos '
            u'selecionados para fechamento!'
        )

    @api.multi
    def button_reopen(self):
        """

        :return:
        """
        for record in self:
            # Abre Períodos
            for period_id in record.mapped('account_period_ids'):
                period_id.reopen_period()

            # Abre Lançamentos ARE
            for move in record.account_move_ids:
                move.state = 'draft'

            # Apaga Lançamentos ARE
            record.account_move_ids.unlink()

            if record.account_move_reclassificacao_id:
                # Abre Lançamento de Reclassificação
                record.account_move_reclassificacao_id.state = 'draft'

                # Apaga Lançamentos da Reclassificação
                record.account_move_reclassificacao_id.unlink()

            if record.account_move_distribuicao_id:
                # Abre Lançamento de Reclassificação
                record.account_move_distribuicao_id.state = 'draft'

                # Apaga Lançamentos da Reclassificação
                record.account_move_distribuicao_id.unlink()

            # Abre o Encerramento
            record.state = 'open'
