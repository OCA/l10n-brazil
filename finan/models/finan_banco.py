# -*- coding: utf-8 -*-
#
# Copyright 2017 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from ..constantes import *


class FinanBanco(SpedBase, models.Model):
    _name = b'finan.banco'
    _description = 'Conta Bancária'
    _rec_name = 'nome'
    _order = 'nome'

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
        store=True,
        index=True,
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
    data_saldo_inicial = fields.Date(
        string='Data do saldo inicial',
    )
    saldo_inicial = fields.Monetary(
        string='Saldo inicial',
    )

    @api.depends('banco', 'agencia', 'conta', 'conta_digito', 'tipo',
                 'titular_id')
    def _compute_banco(self):
        for banco in self:
            nome = FINAN_BANCO_DICT[banco.banco][6:]
            nome += ' / '
            nome += FINAN_TIPO_CONTA_BANCARIA_DICT[banco.tipo]

            if banco.banco != FINAN_BANCO_INTERNO:
                nome += ' / '
                nome += ' ag. '
                nome += banco.agencia

            nome += ' / '
            nome += banco.conta

            if banco.banco != FINAN_BANCO_INTERNO:
                nome += '-'
                nome += banco.conta_digito

            nome += ' / '
            nome += banco.titular_id.name_get()[0][1]

            banco.nome = nome

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
                nome += ' ag. '
                nome += banco.agencia

            nome += ' / '
            nome += banco.conta

            if banco.banco != FINAN_BANCO_INTERNO:
                nome += '-'
                nome += banco.conta_digito

            if not self._context.get('banco_sem_titular'):
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
