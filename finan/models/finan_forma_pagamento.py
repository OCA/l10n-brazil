# -*- coding: utf-8 -*-
#
# Copyright 2017 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import fields, models
from odoo.addons.l10n_br_base.constante_tributaria import (
    FORMA_PAGAMENTO,
    BANDEIRA_CARTAO,
    INTEGRACAO_CARTAO,
    INTEGRACAO_CARTAO_NAO_INTEGRADO,
    FORMA_PAGAMENTO_CARTOES,
    FORMA_PAGAMENTO_CARTAO_CREDITO,
    FORMA_PAGAMENTO_CARTAO_DEBITO,
    FORMA_PAGAMENTO_OUTROS,
    FORMA_PAGAMENTO_DICT,
    BANDEIRA_CARTAO_DICT,
)


class FinanFormaPagamento(models.Model):
    _name = b'finan.forma.pagamento'
    _description = 'Forma de Pagamemento'
    _rec_name = 'nome'
    _order = 'nome'

    nome = fields.Char(
        string='Forma de pagamento',
        size=30,
        required=True,
        index=True,
    )
    quitado_somente_com_data_credito_debito = fields.Boolean(
        string='Considerar dívidas quitadas somente após a confirmação da '
               'data de crédito/débito?',
    )
    exige_numero = fields.Boolean(
        string='Exige número de documento no lançamento dos recebimentos/pagamentos?',
        default=True,
    )
    #
    # Campos para NF-e e SPED
    #
    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        string='Forma de pagamento fiscal',
        default=FORMA_PAGAMENTO_OUTROS,
        required=True,
    )
    bandeira_cartao = fields.Selection(
        selection=BANDEIRA_CARTAO,
        string='Bandeira do cartão',
    )
    integracao_cartao = fields.Selection(
        selection=INTEGRACAO_CARTAO,
        string='Integração do cartão',
        default=INTEGRACAO_CARTAO_NAO_INTEGRADO,
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Operadora do cartão',
        ondelete='restrict',
    )
    #
    # Condições de pagamento vinculadas
    #
    condicao_pagamento_ids = fields.One2many(
        comodel_name='account.payment.term',
        inverse_name='forma_pagamento_id',
        string='Condições de pagamento',
    )
    #
    # Tipo de documento correspondente
    #
    documento_id = fields.Many2one(
        comodel_name='finan.documento',
        string='Tipo de documento',
    )
    #
    # Carteira pra automatizar emissão de boletos
    #
    carteira_id = fields.Many2one(
        comodel_name='finan.carteira',
        string='Carteira',
    )
