# -*- coding: utf-8 -*-
# Copyright 2012 KMEE - Fernando Marcato Rodrigues
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class ResPartnerBank(models.Model):
    """ Adiciona campos necessários para o cadastramentos de contas
    bancárias no Brasil."""
    _inherit = 'res.partner.bank'

    codigo_da_empresa = fields.Integer(
        u'Código da empresa',
        size=20,
        help=u"Será informado pelo banco depois do cadastro do beneficiário "
             u"na agência"
    )

    tipo_de_conta = fields.Selection(
        selection=[
            ('01', u'Conta corrente individual'),
            ('02', u'Conta poupança individual'),
            ('03', u'Conta depósito judicial/Depósito em consignação '
                   u'individual'),
            ('11', u'Conta corrente conjunta'),
            ('12', u'Conta poupança conjunta'),
            ('13', u'Conta depósito judicial/Depósito em consignação '
                   u'conjunta')],
        string=u'Tipo de Conta',
        default='01'
    )

    bra_number = fields.Char(
        size=5,
    )
