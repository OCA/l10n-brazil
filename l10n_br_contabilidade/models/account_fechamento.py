# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pandas as pd

_logger = logging.getLogger(__name__)

from openerp import api, fields, models
from openerp.exceptions import Warning
from openerp import SUPERUSER_ID


class AccountFechamento(models.Model):
    _name = 'account.fechamento'
    _description = 'Modelo para criar os lançamentos de fechamento de períodos'
    _order = 'fiscalyear_id DESC, periodo_ini DESC'
    _inherit = ['ir.needaction_mixin']

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

    account_move_reclassificacao_id = fields.Many2many(
        string=u'Lançamentos da Reclassificação',
        comodel_name='account.move',
        relation='account_fechamento_account_move_reclassificacao_rel',
        column1='account_fechamento_id',
        column2='account_move_id',
    )

    account_move_distribuicao_id = fields.Many2many(
        string=u'Lançamentos da Distribuição',
        comodel_name='account.move',
        relation='account_fechamento_account_move_distribuicao_rel',
        column1='account_fechamento_id',
        column2='account_move_id',
    )

    state = fields.Selection(
        selection=[
            ('open', 'Aberto'),
            ('close', 'Fechado'),
            ('investigated', 'Apurado'),
            ('reclassified', 'Reclassificado'),
            ('completed', 'Concluído'),
        ],
        string='State',
        default='open',
    )

    @api.model
    def _needaction_domain_get(self):
        return [('state', '!=', 'distributed')]

    @api.model
    def _needaction_domain_get(self):
        return [('state', '=', 'close')]

    total_lancamentos_periodos = fields.Integer(
        string=u'Total de lançamentos',
        compute='_compute_total_lancamentos_periodos',
    )

    vl_prejuizo = fields.Float(
        string='Prejuízo',
        compute='_compute_prejuizo',
    )

    justificativa_reabertura_ids = fields.One2many(
        string='Justificativas',
        comodel_name='account.fechamento.reabertura.justificativa',
        inverse_name='fechamento_id',
    )

    @api.multi
    @api.depends('account_move_reclassificacao_id')
    def _compute_prejuizo(self):
        for record in self:
            record.vl_prejuizo = \
                record.account_move_reclassificacao_id.line_id.filtered(
                lambda x: x.account_id == record.conta_reclassificacao(op='P')
                ).debit

    @api.model
    def _needaction_domain_get(self):
        return [('state', 'in',
                 ['open', 'close', 'investigated'])]

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
                raise Warning(u'Períodos já encerrados no '
                              u'intervalo selecionado!')

            # Associa o periodo a este fechamento
            record.account_period_ids = period_ids

    @api.multi
    def _compute_total_lancamentos_periodos(self):
        for record in self:
            total_lancamentos = 0
            for period in record.account_period_ids:
                total_lancamentos += len(period.account_move_ids)

            record.total_lancamentos_periodos = total_lancamentos

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
                raise Warning(u'Períodos já encerrados no '
                                u'intervalo selecionado!')

            # Associa o periodo a este fechamento
            record.account_period_ids = period_ids

    def conta_are(self, op):
        """
        Retorna a conta ARE de acordo com a operação (op) informada
        :param op: D/C (Débito/Crédito)
        :return: account.account
        """
        for record in self:
            return record.account_journal_id.default_credit_account_id \
                if op == 'C' \
                else record.account_journal_id.default_debit_account_id

    def conta_reclassificacao(self, op):
        """
        Retorna a conta de Reclassificação de acordo com a operação (op)
        informada
        :param op: L/P (Lucro/Prejuízo)
        :return: account.account
        """
        for record in self:
            conta_reclassificacao_id = \
                record.account_journal_id.account_lucro_id \
                    if op == 'L' \
                    else record.account_journal_id.account_prejuizo_id

            if not conta_reclassificacao_id:
                raise Warning(
                    u'Configurar as contas de Classificação no Diário!')

            return conta_reclassificacao_id

    def gera_lancamento_partidas(self, move, lines):
        """
        Gera lançamento com partidas

        :param move: Dict{'journal_id': '', 'period_id': '',  'date': ''}
        :param lines: list[Dict{'name': '', 'journal_id': '', 'period_id': '',
        'date': ''}, {...}]

        :return: account.move
        """
        line_list = []
        for record in self:
            for line in lines:
                line_list.append((0, 0, {
                    'account_id': line.get('account_id'),
                    'debit': abs(line.get('debit')),
                    'credit': abs(line.get('credit')),
                    'name': record.account_journal_id.
                    template_historico_padrao_id.get_historico_padrao(),
                }))

            # Gera nome do lançamento a partir do template
            name = record.account_journal_id.\
                template_historico_padrao_id.get_historico_padrao()

            res = record.env['account.move'].sudo(SUPERUSER_ID).create({
                'name': str(name)+'-'+str(move.get('name')),
                'journal_id': move.get('journal_id'),
                'period_id': move.get('period_id'),
                'date': move.get('date'),
                'line_id': line_list,
                'lancamento_de_fechamento': True,
            })

            res.post()

            return res

    def distribuir_resultado(self):
        """
        Lançamentos rateados entre as contas definidas no modelo
        account.journal (Contas para Distribuição de Lucros)
        :return:
        """
        for record in self:

            # Verifica se existe Prejuizo
            if record.vl_prejuizo:
                return True

            # Pega o valor resultado
            account_lucro = record.account_move_reclassificacao_id.line_id.\
                filtered(lambda x: x.account_id == record.
                         conta_reclassificacao(op='L'))

            line_list = []

            resultado = account_lucro.credit

            for seq in set([c.sequencia for c in
                            record.account_journal_id.divisao_resultado_ids]):
                # Credito total da sequência
                credito_total = 0

                for conta in record.account_journal_id.divisao_resultado_ids.\
                        filtered(lambda s: s.sequencia == seq):

                    # Porcentagem/Valor Fixo do item em cima do total restante
                    # do resultado
                    credito = (conta.porcentagem/100)*resultado \
                        if conta.porcentagem != 0.0 else conta.valor_fixo
                    credito_total += credito

                    # Debita da conta de Reclassificação Crédito
                    line_list.append({
                        'account_id': account_lucro.account_id.id,
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
                'name': 'DIST',
                'journal_id': record.account_journal_id.id,
                'period_id': record.periodo_fim.id,
                'date': record.periodo_fim.date_stop,
            }

            # Cria Lançamento e Partidas
            record.account_move_distribuicao_id = \
                record.gera_lancamento_partidas(move=move, lines=line_list)

        return True

    def reclassificar(self):
        """
        Agrupa valores de debito e crédito feitos nas contas ARE.
        Faz lançamentos nas contas definidas como "Contas de Reclassificacação"
         no modelo account.journal de acordo com
        o resultado (Lucro/Prejuízo)
        :return:
        """
        for record in self:
            credito_are = 0
            debito_are = 0

            # Soma valores debito/crédito ARE
            for move in record.account_move_ids:

                credito_are += move.line_id.filtered(
                    lambda x: x.account_id == self.conta_are(op='C')).credit
                debito_are += move.line_id.filtered(
                    lambda x: x.account_id == self.conta_are(op='D')).debit

            resultado = round(credito_are, 6) - round(debito_are, 6)

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
            if line_list:
                move = {
                    'name': 'RECLAS',
                    'journal_id': record.account_journal_id.id,
                    'period_id': record.periodo_fim.id,
                    'date': record.periodo_fim.date_stop,
                    'lancamento_de_fechamento': True,
                }

                # Associa lançamento ao encerramento
                record.account_move_reclassificacao_id = \
                    record.gera_lancamento_partidas(move=move, lines=line_list)

        return True

    def apurar_periodos(self):
        """
        Apura Períodos
        :return:
        """
        for record in self:

            # Lançamentos de todos períodos do fechamento
            account_move_ids = \
                record.account_period_ids.mapped('account_move_ids')

            are_debito = record.account_journal_id.default_debit_account_id.id
            are_credito = record.account_journal_id.default_credit_account_id.id

            if not are_credito or not are_debito:
                raise Warning(
                    u'Configurar as contas ARE no Lote de '
                    u'Lançamentos de fechamentos')

            # Popula o dataframe com valores do account.move.line
            df_are = pd.DataFrame(
            account_move_ids.mapped('line_id').filtered(
                lambda x: x.account_id.user_type.report_type in (
                'income', 'expense')).mapped(
                lambda r: {'conta': r.account_id.id, 'debito': r.debit,
                           'credito': r.credit, 'periodo': r.period_id.id,
                           'dt_stop': r.period_id.date_stop}),
                columns=['conta', 'debito', 'credito', 'periodo', 'dt_stop'])

            # Agrupa por conta e soma as outras colunas
            df_agrupado = df_are.groupby('conta').sum()
            df_agrupado['result'] = \
                (df_agrupado['debito'] - df_agrupado['credito'])

            if len(df_agrupado) == 0:
                raise Warning(u'Nenhuma conta de resultado encontrada. '
                              u'Não é possível prosseguir.')

            for conta in df_agrupado.index:
                series_conta = df_agrupado.loc[conta]
                if round(series_conta['result'], 6) != 0.0:

                    if series_conta['result'] > 0.0:
                        conta_id = {
                            'account_id': int(conta),
                            'debit': 0.0,
                            'credit': series_conta['result'],
                            'name': record.account_journal_id.
                            template_historico_padrao_id.
                            get_historico_padrao(),
                        }

                        are_id = {
                            'account_id': int(are_debito),
                            'debit': series_conta['result'],
                            'credit': 0.0,
                            'name': record.account_journal_id.
                            template_historico_padrao_id.
                            get_historico_padrao(),
                        }

                    elif series_conta['result'] < 0.0:
                        conta_id = {
                            'account_id': int(conta),
                            'debit': abs(series_conta['result']),
                            'credit': 0.0,
                            'name': record.account_journal_id.
                            template_historico_padrao_id.
                            get_historico_padrao(),
                        }

                        are_id = {
                            'account_id': int(are_credito),
                            'debit': 0.0,
                            'credit': abs(series_conta['result']),
                            'name': record.account_journal_id.
                            template_historico_padrao_id.
                            get_historico_padrao(),
                        }

                    record.env['account.move'].sudo(SUPERUSER_ID).create({
                        'journal_id': record.account_journal_id.id,
                        'period_id': record.periodo_fim.id,
                        'date': record.periodo_fim.date_stop,
                        'state': 'draft',
                        'lancamento_de_fechamento': True,
                        'account_fechamento_id': record.id,
                        'line_id': [(0, 0, conta_id), (0, 0, are_id)]
                    }).post()

        return True

    @api.multi
    def fechar_periodos(self):
        """

        :return:
        """
        for record in self:
            record.button_buscar_periodos()
            for period_id in record.account_period_ids:
                period_id.account_journal_id = record.account_journal_id
                period_id.fechar_periodo()

        return True

    @api.multi
    def button_forward(self):
        """
        Avança de acordo com o estágio do Lançamento.

        :return:
        """
        for record in self:
            if record.state == 'open':
                if record.fechar_periodos():
                    record.state = 'close'

            elif record.state == 'close':
                if record.apurar_periodos():
                    record.state = 'investigated'

            elif self.state == 'investigated':
                if record.reclassificar():
                    a_prej = record.account_move_reclassificacao_id. \
                        line_id. \
                        filtered(lambda x: x.account_id == record.
                                 conta_reclassificacao(op='P'))

                    record.state = 'completed' if a_prej else 'reclassified'

            elif self.state == 'reclassified':
                if record.distribuir_resultado():
                    record.state = 'completed'

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def button_goback(self, justificativa_id=False):
        for record in self:
            if record.state == 'close':
                # Abre Períodos
                if justificativa_id:
                    for period_id in record.mapped('account_period_ids'):
                        self.reabertura_periodos_fechamento(
                            period_id, justificativa_id
                        )

                record.state = 'open'  # Retorna state p/ "Aberto"

            if record.state == 'investigated':
                for move in record.account_move_ids:
                    move.state = 'draft'  # Abre Lançamento ARE

                record.account_move_ids.unlink()  # Apaga Lançamentos ARE
                record.state = 'close'  # Retorna state p/ "Fechado"

            if record.state == 'reclassified':
                if record.account_move_reclassificacao_id:
                    # Abre Lançamento de Reclassificação
                    record.account_move_reclassificacao_id.state = 'draft'

                    # Apaga Lançamentos da Reclassificação
                    record.account_move_reclassificacao_id.unlink()
                record.state = 'investigated'  # Retorna state p/ "Apurado"

            if record.state == 'completed':
                if record.account_move_distribuicao_id:
                    # Abre Lançamento de Reclassificação
                    record.account_move_distribuicao_id.state = 'draft'

                    # Abre Períodos
                    if justificativa_id:
                        for period_id in record.mapped('account_period_ids'):
                            self.reabertura_periodos_fechamento(
                                period_id, justificativa_id
                            )

                    # Apaga Lançamentos da Reclassificação
                    record.account_move_distribuicao_id.unlink()
                record.state = 'reclassified'  # Retorna state p/ "Reclass."

    def _get_justificativa_periodo_values(self, period_id, justificativa_id):
        vals = {
            'employee_id': justificativa_id.employee_id.id,
            'data': justificativa_id.data,
            'motivo': justificativa_id.motivo,
            'period_id': period_id.id,
        }

        return vals

    def reabertura_periodos_fechamento(self, period_id, justificativa_id):
        justificativa_periodo_id = \
            self.env['account.reabertura.periodo.justificativa']
        justificativa_periodo_id.create(
            self._get_justificativa_periodo_values(period_id, justificativa_id)
        )
        period_id.state = 'validate'

    @api.multi
    def button_reopen(self, justificativa_id=False):
        """

        :return:
        """
        for record in self:
            # Abre Períodos
            # Abre Períodos
            if justificativa_id:
                for period_id in record.mapped('account_period_ids'):
                    self.reabertura_periodos_fechamento(
                        period_id, justificativa_id
                    )

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
