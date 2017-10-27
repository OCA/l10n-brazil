# -*- coding: utf-8 -*-
#
# Copyright 2017 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging
import json

from odoo import api, fields, models
from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from ..constantes import *

_logger = logging.getLogger(__name__)

try:
    from pybrasil.data import hoje
    from pybrasil.valor import formata_valor
    from pybrasil.valor.decimal import Decimal as D, json_decimal_default
    json._default_encoder.default = json_decimal_default

except (ImportError, IOError) as err:
    _logger.debug(err)


class FinanBanco(SpedBase, models.Model):
    _name = b'finan.banco'
    _description = 'Conta Bancária'
    _rec_name = 'nome'
    #_order = 'nome'

    banco = fields.Selection(
        selection=FINAN_BANCO,
        required=True,
        index=True,
    )
    agencia = fields.Char(
        string='Agência',
        size=5,
    )
    agencia_digito = fields.Char(
        string='Dígito da agência',
        size=1,
    )
    conta = fields.Char(
        string='Conta',
        size=10,
        required=True,
    )
    conta_digito = fields.Char(
        string='Dígito da conta',
        size=1,
    )
    tipo = fields.Selection(
        selection=FINAN_TIPO_CONTA_BANCARIA,
        string='Tipo',
        default=FINAN_TIPO_CONTA_BANCARIA_CAIXA,
        required=True,
        index=True,
    )
    nome = fields.Char(
        string='Conta bancária',
        size=500,
        compute='_compute_banco',
        #store=True,
        #index=True,
    )
    titular_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Titular',
        domain=[('cnpj_cpf', '!=', False)],
        required=True,
        index=True,
    )
    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        compute='_compute_cnpj_cpf',
        store=True,
        index=True,
    )
    cnpj_cpf_raiz = fields.Char(
        string='Raiz do CNPJ/CPF',
        compute='_compute_cnpj_cpf',
        store=True,
        index=True,
    )
    #data_saldo_inicial = fields.Date(
        #string='Data do saldo inicial',
    #)
    #saldo_inicial = fields.Monetary(
        #string='Saldo inicial',
    #)
    saldo_atual = fields.Monetary(
        string='Saldo atual',
        compute='_compute_saldo_atual',
    )
    extrato_ids = fields.One2many(
        comodel_name='finan.banco.extrato',
        inverse_name='banco_id',
        readonly=True,
    )

    #
    # Dashboards
    #
    dashboard_saldo_hoje = fields.Text(
        compute='_compute_dashboard_saldo_hoje'
    )

    @api.depends('banco', 'agencia', 'conta', 'conta_digito', 'tipo',
                 'titular_id')
    def _compute_banco(self):
        for banco in self:
            banco.nome = banco.name_get()[0][1]

    def _compute_saldo_atual(self):
        for banco in self:
            saldo = self.env['finan.banco.saldo'].search([
                ('banco_id', '=', banco.id),
                ('data', '<=', str(hoje())),
                ], limit=1, order='data desc')

            if saldo:
                banco.saldo_atual = saldo.saldo

    @api.depends('titular_id', 'titular_id.cnpj_cpf')
    def _compute_cnpj_cpf(self):
        for banco in self:
            banco.cnpj_cpf = banco.titular_id.cnpj_cpf
            banco.cnpj_cpf_raiz = banco.titular_id.cnpj_cpf_raiz

    def name_get(self):
        res = []

        for banco in self:
            nome = FINAN_BANCO_DICT[banco.banco][6:]
            nome += ' / '
            nome += FINAN_TIPO_CONTA_BANCARIA_DICT[banco.tipo]

            if banco.banco != FINAN_BANCO_INTERNO:
                nome += ' / '
                nome += banco.agencia

            nome += ' / '
            nome += banco.conta

            if banco.banco != FINAN_BANCO_INTERNO:
                nome += '-'
                nome += banco.conta_digito

            if not self.env.context.get('banco_sem_titular'):
                nome += ' / '
                nome += banco.titular_id.name_get()[0][1]

            res.append((banco.id, nome))

        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name and operator in ('=', 'ilike', '=ilike', 'like'):
            if operator != '=':
                name = name.strip().replace(' ', '%')

            args += [
                '|',
                ('banco', '=', name),
                '|',
                ('agencia', 'ilike', name),
                '|',
                ('conta', 'ilike', name),
                ('titular_id', 'ilike', name),
            ]
            bancos = self.search(args, limit=limit)
            return bancos.name_get()

        return super(FinanBanco, self).name_search(name=name, args=args,
                                                         operator=operator,
                                                         limit=limit)

    def dados_dashboard_saldo_hoje(self):
        self.ensure_one()

        dados = {
            'titulo': FINAN_TIPO_CONTA_BANCARIA_DICT[self.tipo],
            'banco': self.with_context(banco_sem_titular=True).nome,
            'titular': self.titular_id.name_get()[0][1],
            'currency_id': self.currency_id.id,
        }
        entrada = D(0)
        saida = D(0)
        saldo = D(0)

        #
        # Busca os dados de hoje
        #
        saldo_dia = self.env['finan.banco.saldo'].search(
            [('banco_id', '=', self.id), ('data', '<=', str(hoje()))],
            order='data desc',
            limit=1,
        )

        if saldo_dia:
            entrada = D(saldo_dia.entrada)
            saida = D(saldo_dia.saida)
            saldo = D(saldo_dia.saldo)

        dados['entrada'] = self.currency_id.symbol + ' ' + \
            formata_valor(entrada)
        dados['saida'] = self.currency_id.symbol + ' ' + \
            formata_valor(saida)
        dados['saldo'] = self.currency_id.symbol + ' ' + \
            formata_valor(saldo)

        return dados

    def _compute_dashboard_saldo_hoje(self):
        for banco in self:
            banco.dashboard_saldo_hoje = \
                json.dumps(banco.dados_dashboard_saldo_hoje())
