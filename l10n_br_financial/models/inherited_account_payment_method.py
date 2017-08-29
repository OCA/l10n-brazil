# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class AccountPaymentMethod(models.Model):

    _inherit = b'account.payment.method'

    codigo = fields.Char(
        string='Código',
        help='Código da carteira de cobrança',
    )
    codigo_cnab = fields.Char(
        string='Código CNAB',
    )

    variacao = fields.Char(
        string='Váriação',
    )

    # descrição
    # convenio
    # digito
    # conta
    # correnta

    # nosso número
    # variação
    #
    # aceite
    # especie
    # modalidade
    # pré-impresso
    # imprime numero do documento nas instruções
    #
    # sequencia nosso número
