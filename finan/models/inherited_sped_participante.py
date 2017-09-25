# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from ..constantes import *


class SpedParticipante(models.Model):
    _inherit = 'sped.participante'

    limite_credito = fields.Monetary(
        string='Limite de crédito',
    )
    limite_credito_disponivel = fields.Monetary(
        string='Limite disponível',
        compute='_compute_limite_credito',
        store=True,
    )
    saldo_a_receber = fields.Monetary(
        string='Saldo devedor a receber',
        compute='_compute_limite_credito',
        store=True,
    )
    saldo_a_pagar = fields.Monetary(
        string='Saldo devedor a pagar',
        compute='_compute_limite_credito',
        store=True,
    )
    adiantamento_a_pagar = fields.Monetary(
        string='Adiantamentos a pagar',
        compute='_compute_limite_credito',
        store=True,
    )
    adiantamento_a_receber = fields.Monetary(
        string='Adiantamentos a receber',
        compute='_compute_limite_credito',
        store=True,
    )
    divida_ids = fields.One2many(
        comodel_name='finan.lancamento',
        inverse_name='participante_id',
        string='Dívidas',
        domain=[('tipo', '=', FINAN_TIPO_DIVIDA)],
    )
    pagamento_ids = fields.One2many(
        comodel_name='finan.lancamento',
        inverse_name='participante_id',
        string='Pagamentos',
        domain=[('tipo', '=', FINAN_TIPO_PAGAMENTO)],
    )

    @api.depends('limite_credito',
                  'divida_ids.vr_saldo',
                  'divida_ids.provisorio',
                  'divida_ids.situacao_divida_simples',
                  'pagamento_ids.vr_adiantado',
                  'pagamento_ids.situacao_divida_simples')
    def _compute_limite_credito(self):
        for participante in self:
            if not participante.id:
                continue

            sql_dividas = '''
            select
                coalesce(sum(coalesce(fl.vr_saldo, 0)), 0) as saldo
            from
                finan_lancamento fl
            where
                fl.tipo = '{tipo}'
                and fl.participante_id = {participante_id}
                and fl.provisorio != True
                and fl.situacao_divida_simples = 'aberto';
            '''
            sql = sql_dividas.format(tipo=FINAN_DIVIDA_A_RECEBER,
                                     participante_id=participante.id)
            self.env.cr.execute(sql)
            saldo_a_receber = self.env.cr.fetchall()[0][0]

            sql = sql_dividas.format(tipo=FINAN_DIVIDA_A_PAGAR,
                                     participante_id=participante.id)
            self.env.cr.execute(sql)
            saldo_a_pagar = self.env.cr.fetchall()[0][0]

            sql_adiantamento = '''
            select
                coalesce(sum(coalesce(fl.vr_adiantado, 0)), 0) as vr_adiantado
            from
                finan_lancamento fl
            where
                fl.tipo = '{tipo}'
                and fl.participante_id = {participante_id}
                and fl.situacao_divida_simples = 'quitado';
            '''

            sql = sql_adiantamento.format(
                tipo=FINAN_RECEBIMENTO,
                participante_id=participante.id
            )
            self.env.cr.execute(sql)
            adiantamento_a_pagar = self.env.cr.fetchall()[0][0]

            sql = sql_adiantamento.format(
                tipo=FINAN_PAGAMENTO,
                participante_id=participante.id
            )
            self.env.cr.execute(sql)
            adiantamento_a_receber = self.env.cr.fetchall()[0][0]

            if participante.limite_credito:
                limite_credito_disponivel = participante.limite_credito
                limite_credito_disponivel -= saldo_a_receber
            else:
                limite_credito_disponivel = 0

            participante.saldo_a_receber = saldo_a_receber
            participante.saldo_a_pagar = saldo_a_pagar
            participante.adiantamento_a_pagar = adiantamento_a_pagar
            participante.adiantamento_a_receber = adiantamento_a_receber
            participante.limite_credito_disponivel = limite_credito_disponivel
