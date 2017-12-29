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
    _order = 'data_final DESC'
    _rec_name = 'banco_id'

    saldo_inicial = fields.Float(
        string='Saldo inicial',
        compute='_compute_saldo_inicial',
        store=True,
    )

    saldo_final = fields.Float(
        string='Saldo final',
        compute = '_compute_saldo_final',
    )

    lancamento_ids = fields.Many2many(
        string='Lancamentos',
        comodel_name='finan.lancamento',
        readonly=True,
        states={'aberto': [('readonly', False)]},
    )

    saldo = fields.Float(
        string="Saldo dos lançamentos",
        compute='_compute_saldo_final',
    )

    banco_id = fields.Many2one(
        comodel_name='finan.banco',
        string='Banco/caixa',
        index=True,
        ondelete='restrict',
        required=True,
        readonly=True,
        states={'aberto':[('readonly', False)]},
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
        required=True,
        help='Data do último fechamento somada em um dia.',
        default=lambda self: self.compute_data_inicial(),
        readonly=True,
        states={'aberto': [('readonly', False)]},
    )

    data_final = fields.Date(
        string='Data final',
        index=True,
        required=True,
        readonly=True,
        states={'aberto': [('readonly', False)]},
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
        for fechamento_id in self:
            if fechamento_id.data_inicial > fechamento_id.data_final:
                raise ValidationError(
                    'A data final deve ser maior que a data inicial')

    @api.multi
    def button_processar(self):
        """
        Recuperar os lancamentos entre a data_inicial e data_final do 
        fechamento do caixa, e calcular o saldo do banco
        """
        for fechamento_id in self:

            lancamento_ids = self.env.get('finan.lancamento').search([
                ('banco_id', '=', fechamento_id.banco_id.id),
                ('data_pagamento', '>=', fechamento_id.data_inicial),
                ('data_pagamento', '<=', fechamento_id.data_final),
                ('tipo', 'in', ['recebimento', 'pagamento']),
            ])

            fechamento_id.lancamento_ids = lancamento_ids

    @api.multi
    def button_fechar_caixa(self):
        """
        Rotina para fechamento de caixa onde altera o state do fechamento
        """
        for fechamento_id in self:
            fechamento_id.state = 'fechado'
            fechamento_id.data_fechamento = fields.Date.today()

    @api.multi
    def button_reabrir_caixa(self):
        for fechamento_id in self:
            if fechamento_id.user_id.has_group('finan.GRUPO_CADASTRO_GERENTE'):
                fechamento_id.state = 'aberto'
                fechamento_id.data_fechamento = False

    @api.constrains('data_final', 'data_inicial', 'banco_id')
    def validacao_fechamentos(self):
        """
        Funcao valida se o intervalo que se pretende criar deixara algum dia
         fora de um intervalo. Se ja houver um intervalo inserido, um novo 
         intervalo deve comecar imediatamente depois dele ou terminar antes 
         do comeco dele.        
        """
        for fechamento_id in self:

            # Buscar todos fechamentos ordenados por data_final,
            #  excluindo o lancamento corrente
            #
            fechamentos_ids = self.search([
                ('banco_id', '=', fechamento_id.banco_id.id),
                ('id', '!=', fechamento_id.id),
            ], limit=1, order='data_final DESC')

            # Se nao achar nenhum cadastrado, permitir qualquer data
            #
            if not fechamentos_ids:
                return

            # Ultima data do ultimo lançamento
            #
            ultima_data = \
                fields.Date.from_string(fechamentos_ids.data_final)

            #
            #
            if ultima_data + relativedelta(days=1) != \
                    fields.Date.from_string(fechamento_id.data_inicial):
                raise ValidationError(
                    'Existem datas entre fechamentos, que nao pertecem a '
                    'nenhum fechamento de caixa ou uma das datas ja fazem '
                    'parte de algum fechamento existente')


    @api.depends('banco_id')
    def compute_data_inicial(self):
        """
        Método para computar a data inicial, baseado na data_final do ultimo
        fechamento de caixa.
        """
        for fechamento_id in self:
            if fechamento_id.banco_id:
                fechamentos_ids = self.search([
                    ('banco_id', '=', fechamento_id.banco_id.id),
                ], limit=1, order='data_final DESC')

                if not fechamentos_ids:
                    return

                data_inicial = \
                    fields.Date.from_string(fechamentos_ids.data_final) + \
                    relativedelta(days=1)

                return str(data_inicial)

    @api.multi
    @api.depends('lancamento_ids')
    def _compute_saldo_final(self):
        """
        Funcao computa o saldo final baseado nos lançamentos
        e no saldo inicial
        """
        saldo = 0
        for lancamento_id in self:
            for valores in lancamento_id.lancamento_ids:
                if valores.tipo == 'recebimento':
                    saldo += valores.vr_total
                elif valores.tipo == 'pagamento':
                    saldo -= valores.vr_total

            lancamento_id.saldo_final = lancamento_id.saldo_inicial + saldo
            lancamento_id.saldo = saldo

    @api.depends('lancamento_ids')
    def _compute_saldo_inicial(self):
        """
        Funcao computa o saldo final do lançamento
        anterior

        """
        for fechamento_id in self:
            if fechamento_id.banco_id:
                fechamentos_ids = self.search([
                    ('banco_id', '=', fechamento_id.banco_id.id),
                    ('id', '!=', fechamento_id.id),
                ], limit=1, order='data_final DESC')

                if not fechamentos_ids:
                    fechamento_id.saldo_inicial = 0.0

                fechamento_id.saldo_inicial = fechamentos_ids.saldo_final

    # @api.depends('banco_id')
    # def compute_data_inicial(self):
    #     """
    #     Método para computar a data inicial, baseado na data_final do ultimo
    #     fechamento de caixa.
    #     """
    #     for fechamento_id in self:
    #         if fechamento_id.banco_id:
    #             fechamentos_ids = self.search([
    #                 ('banco_id', '=', fechamento_id.banco_id.id),
    #             ], limit=1, order='data_final DESC')
    #
    #             if not fechamentos_ids:
    #                 return
    #
    #             fechamento_id.data_inicial = \
    #                 fields.Date.from_string(fechamentos_ids.data_final) + \
    #                 relativedelta(days=1)
