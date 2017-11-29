# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from dateutil.relativedelta import relativedelta


class FinanBancoFechamento(models.Model):
    _name = b'finan.banco.fechamento'
    _description = 'Fechamento de Caixa'

    saldo_inicial = fields.Float(
        string='Saldo inicial',
    )

    saldo_final = fields.Float(
        string='Saldo final',
        # compute = '_compute_saldo_final'
    )

    lancamento_ids = fields.Many2many(
        string='Lancamentos',
        comodel_name='finan.lancamento',
        readonly=True,
        states={'aberto': [('readonly', False)]},
    )

    saldo = fields.Float(
        string="Saldo dos lancamentos"
    )

    banco_id = fields.Many2one(
        comodel_name='finan.banco',
        string='Banco/caixa',
        index=True,
        ondelete='restrict',
        required=True,
    )

    user_id = fields.Many2one(
        string='Quem fechou?',
        comodel_name='res.users',
        default=lambda self: self.env.user.id,
        required=True,
    )

    data_fechamento = fields.Date(
        string='Data do fechamento',
        index=True,
        readonly=True,
    )

    data_inicial = fields.Date(
        string='Data inicial',
        index=True,
        required=True,
    )

    data_final = fields.Date(
        string='Data final',
        index=True,
        required=True,
    )

    state = fields.Selection(
        string='State',
        selection=[
            ('aberto', 'Aberto'),
            ('fechado', 'Fechado'),
        ],
        default='aberto',
    )


    @api.constrains('data_final', 'data_inicial')
    def _constrains_verifica_data(self):
        """
        Validacao para a data final ser maior que a data inicial
        """
        for record in self:
            if record.data_inicial > record.data_final:
                raise ValidationError(
                    'A data final deve ser maior que a data inicial')


    def button_processar(self):
        """
        Recuperar os lancamentos entre a data_inicial e data_final do 
        fechamento do caixa, e calcular o saldo do banco
        """
        for banco in self:
            lancamento_ids = self.env.get('finan.lancamento').search([
                ('banco_id', '=', banco.id) and
                ('data_documento', '>=', banco.data_inicial) and
                ('data_documento', '<=', banco.data_final),
                # ('state', '=', 'paid'),
            ])
            if (('data_documento', '>=', banco.data_inicial) and
                ('data_documento', '<=', banco.data_final)):
                banco.lancamento_ids = lancamento_ids
            # saldo = self.env['finan.banco.saldo'].search([
            #             ('banco_id', '=', banco.id),
            #             ('data', '<=', str(hoje())),
            #         ], limit=1, order='data desc')
            #         if saldo:
            #             self.saldo_final = saldo.saldo + self.saldo_inicial
            #         else:
            #             self.saldo_final = self.saldo_inicial

    def button_fechar_caixa(self):
        """
        Rotina para fechamento de caixa onde altera o state do fechamento
        """
        for banco in self:
            banco.state = 'fechado'
            banco.data_fechamento = fields.Date.today()


    # def _compute_saldo_final(self):
    #     """
    #             Calculo do saldo final: movimentos + inicial
    #     """
    #     for banco in self:
    #         saldo = self.env['finan.banco.saldo'].search([
    #             ('banco_id', '=', banco.id),
    #             ('data', '<=', str(hoje())),
    #         ], limit=1, order='data desc')
    #         if saldo:
    #             self.saldo_final = saldo.saldo + self.saldo_inicial
    #         else:
    #             self.saldo_final = self.saldo_inicial


    @api.constrains('data_final', 'data_inicial')
    def validacao_fechamentos(self):

        '''
        Funcao valida se o intervalo que se pretende criar deixara algum dia fora de um intervalo.
        Se ja houver um intervalo inserido,
        um novo intervalo deve comecar imediatamente depois dele ou
        terminar antes do comeco dele.
        :return:
        '''

        inicio = fields.Date.from_string(self.data_inicial)
        count = self.search_count([('banco_id', '=', self.banco_id.id)])

        resposta = 0
        aux = count

        for record in self.search([('banco_id', '=', self.banco_id.id)]):
            aux -= 1
            if aux == 0:
                break
            else:
                data_inicio = fields.Date.from_string(record.data_inicial)
                data_fim = fields.Date.from_string(record.data_final)

                if inicio == data_inicio:
                    resposta = 0

                if (inicio - data_fim).days == 1:
                    resposta = 1


        if resposta == 0 and count!=1:
            raise ValidationError('Existem datas entre fechamentos, '
                    'que nao pertecem a nenhum fechamento de caixa ou uma das datas ja fazem parte '
                    ' de algum fechamento existente')









