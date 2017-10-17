# -*- coding: utf-8 -*-
# Copyright 2012 KMEE - Fernando Marcato Rodrigues
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, models, fields
from ..constantes import TIPO_SERVICO, FORMA_LANCAMENTO, \
    INDICATIVO_FORMA_PAGAMENTO, TIPO_MOVIMENTO, CODIGO_INSTRUCAO_MOVIMENTO


class PaymentOrder(models.Model):
    _inherit = b'payment.order'

    file_number = fields.Integer(
        string=u'Número sequencial do arquivo',
    )

    cnab_file = fields.Binary(
        string='CNAB File',
        readonly=True,
    )

    cnab_filename = fields.Char("CNAB Filename")

    tipo_servico = fields.Selection(
        selection=TIPO_SERVICO,
        string=u'Tipo de Serviço',
        help=u'Campo G025 do CNAB',
        default='30',
    )
    forma_lancamento = fields.Selection(
        selection=FORMA_LANCAMENTO,
        string=u'Forma Lançamento',
        help=u'Campo G029 do CNAB'
    )
    codigo_convenio = fields.Char(
        size=20,
        string=u'Código do Convênio no Banco',
        help=u'Campo G007 do CNAB',
        default=u'0001222130126',
    )
    indicativo_forma_pagamento = fields.Selection(
        selection=INDICATIVO_FORMA_PAGAMENTO,
        string=u'Indicativo de Forma de Pagamento',
        help='Campo P014 do CNAB',
        default='01'
    )
    tipo_movimento = fields.Selection(
        selection=TIPO_MOVIMENTO,
        string='Tipo de Movimento',
        help='Campo G060 do CNAB',
        default='0',
    )
    codigo_instrucao_movimento = fields.Selection(
        selection=CODIGO_INSTRUCAO_MOVIMENTO,
        string='Código da Instrução para Movimento',
        help='Campo G061 do CNAB',
        default='0',
    )

    # @api.multi
    # def set_to_draft(self, *args):
    #     super(PaymentOrder, self).set_to_draft(*args)
    #
    #     for order in self:
    #         for line in order.line_ids:
    #             self.write_added_state_to_move_line(line.move_line_id)
    #     return True

    # @api.multi
    # def write_added_state_to_move_line(self, mov_line):
    #     mov_line.state_cnab = 'added'
