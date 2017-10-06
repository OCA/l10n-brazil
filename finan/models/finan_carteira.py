# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from ..constantes import *


class FinanCarteira(SpedBase, models.Model):
    _name = b'finan.carteira'
    _description = 'Carteira de Boletos'
    _rec_name = 'nome'
    #_order = 'nome'

    nome = fields.Char(
        string='Nome',
        compute='_compute_nome',
        #store=True,
        #index=True,
    )
    banco_id = fields.Many2one(
        comodel_name='finan.banco',
        string='Conta bancária',
        required=True,
        index=True,
        domain="[('banco', '!=', '000')]",  # Carteiras não podem usar o
                                            # banco interno
    )
    #
    # Alguns bancos usam o leiaute de outro nas remessas
    #
    banco = fields.Selection(
        selection=FINAN_BANCO_CHEQUE_BOLETO,
    )

    #
    # Os campos abaixo têm nomes diferentes conforme o banco,
    # e nem todo banco usa todos os campos, é uma zona!
    #
    carteira = fields.Char(
        string='Carteira',
        size=10,
        required=True,
    )
    beneficiario = fields.Char(
        string='Beneficiário',
        size=20,
        required=True,
    )
    beneficiario_digito = fields.Char(
        string='Dígito do beneficiário',
        size=1,
        required=True,
    )
    sacador_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Sacador avalista',
        ondelete='restrict',
    )

    #
    # Variam conforme o banco
    #
    convenio = fields.Char(
        string='Convênio',
        size=10,
    )
    modalidade = fields.Char(
        string='Modalidade',
        size=10,
    )

    #
    # Dependem de negociação com o banco (entrega via correio)
    #
    banco_emite = fields.Boolean(
        string='Emissão (nosso número) pelo banco?',
    )
    banco_entrega = fields.Boolean(
        string='Entrega pelo banco?',
    )

    #
    # Juros e multa
    #
    al_juros = fields.Monetary(
        string='Taxa de juros (mensal)',
        currency_field='currency_aliquota_id'
    )
    al_multa = fields.Monetary(
        string='Percentual de multa',
        currency_field='currency_aliquota_id'
    )

    #
    # Protesto e outros controles por dias
    #
    dias_protesto = fields.Integer(
        string='Dias para protesto',
    )
    dias_nao_recebimento = fields.Integer(
        string='Dias para não recebimento',
    )
    dias_negativacao = fields.Integer(
        string='Dias para negativação',
    )

    #
    # Controle da numeração dos boletos e arquivos,
    # não podemos usar o sequence aqui, pois alguns bancos
    # usam uma numeração imensa, alguns com uma quantidade de dígitos
    # específica, às vezes até 15 dígitos!
    #
    proximo_nosso_numero = fields.Char(
        string='Próximo nosso número',
        size=20,
        required=True,
        default='1',
    )
    proxima_remessa = fields.Integer(
        string='Próxima remessa',
        required=True,
        default=1,
    )

    @api.depends('banco_id', 'banco_id.banco', 'banco_id.titular_id',
                 'carteira',
                 'beneficiario', 'beneficiario_digito')
    def _compute_nome(self):
        for carteira in self:
            nome = carteira.banco_id.nome.split('/')[0].strip()
            nome += ' / '
            nome += carteira.carteira
            nome += ' / '
            nome += carteira.beneficiario
            nome += '-'
            nome += carteira.beneficiario_digito

            if not self.env.context.get('banco_sem_titular'):
                nome += ' / '
                nome += carteira.banco_id.titular_id.name_get()[0][1]

            carteira.nome = nome
