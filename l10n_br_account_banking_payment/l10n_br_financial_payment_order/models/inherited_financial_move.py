# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models, _

from pybrasil.febraban import (valida_codigo_barras, valida_linha_digitavel,
    identifica_codigo_barras, monta_linha_digitavel, monta_codigo_barras,
    formata_linha_digitavel)

import base64

from ..febraban.boleto.document import Boleto
from ..febraban.boleto.document import BoletoException

from datetime import date
import logging
_logger = logging.getLogger(__name__)


from ..constantes import TIPO_SERVICO, TIPO_SERVICO_COMPLEMENTO, \
    FORMA_LANCAMENTO, BOLETO_ESPECIE


class FinancialMove(models.Model):
    _inherit = b'financial.move'

    #
    # Integração bancária via CNAB
    #
    payment_mode_id = fields.Many2one(
        comodel_name='payment.mode',
        string='Carteira de cobrança',
        ondelete='restrict',
    )
    tipo_pagamento = fields.Selection(
        related='payment_mode_id.tipo_pagamento',
        store=True
    )
    #
    # Implementa o nosso número como NUMERIC no Postgres, pois alguns
    # bancos têm números bem grandes, que não dão certo com integers
    #
    nosso_numero = fields.Float(
        string='Nosso número',
        digits=(21, 0),
    )
    #
    # Para pagamentos automatizados de boletos de terceiros
    #
    boleto_linha_digitavel = fields.Char(
        string='Linha digitável',
        size=55,
    )
    boleto_codigo_barras = fields.Char(
        string='Código de barras',
        size=44,
    )

    def _trata_linha_digitavel(self):
        self.ensure_one()

        if not self.boleto_linha_digitavel:
            return

        #
        # Foi informado o número via leitura do codigo de barras?
        #
        if valida_codigo_barras(self.boleto_linha_digitavel):
            codigo_barras = self.boleto_linha_digitavel
            linha_digitavel = monta_linha_digitavel(codigo_barras)
        #
        # Ou foi informado via digitação mesmo?
        #
        elif valida_linha_digitavel(self.boleto_linha_digitavel):
            codigo_barras = monta_codigo_barras(self.boleto_linha_digitavel)
            linha_digitavel = \
                formata_linha_digitavel(self.boleto_linha_digitavel)

        else:
            return
            #raise código inválido

        identificacao = identifica_codigo_barras(codigo_barras)

        if identificacao is None:
            return
            #raise código inválido

        self.boleto_linha_digitavel = linha_digitavel
        self.boleto_codigo_barras = codigo_barras

        if 'valor' in identificacao:
            self.amount_document = identificacao['valor']

        if 'vencimento' in identificacao and \
                identificacao['vencimento'] is not None:
            self.date_maturity = str(identificacao['vencimento'])

    @api.multi
    @api.onchange('boleto_linha_digitavel')
    def _onchange_linha_digitavel(self):
        for move in self:
            move._trata_linha_digitavel()

    @api.multi
    @api.depends('boleto_linha_digitavel')
    def _depends_linha_digitavel(self):
        for move in self:
            move._trata_linha_digitavel()

    @api.multi
    def button_boleto(self):
        self.ensure_one()

        # action = self.env['report'].get_action(
        #     self, b'l10n_br_financial_payment_order.report')

        action = self.env['report'].get_action(
            self, b'l10n_br_financial_payment_order.boleto_py3o')

        return action

    @api.multi
    def gera_boleto(self):

        boleto_list = []

        for financial_move in self:
            try:

                # if True:
                # if financial_move.payment_mode_id.type_payment == '00':
                #     number_type = financial_move.company_id.own_number_type
                #     if not financial_move.boleto_own_number:
                #         if number_type == '0':
                #             nosso_numero = self.env['ir.sequence'].next_by_id(
                #                 financial_move.company_id.own_number_sequence.id)
                #         elif number_type == '1':
                #             nosso_numero = \
                #                 financial_move.transaction_ref.replace('/', '')
                #         else:
                #             nosso_numero = self.env['ir.sequence'].next_by_id(
                #                 financial_move.payment_mode_id.
                #                 internal_sequence_id.id)
                #     else:
                #         nosso_numero = financial_move.boleto_own_number

                    seq_id = \
                        financial_move.payment_mode_id.\
                            sequence_nosso_numero_id.id
                    nosso_numero = str(int(self.nosso_numero)) or \
                                   self.env['ir.sequence'].next_by_id(seq_id)


                    boleto = Boleto.getBoleto(financial_move, nosso_numero)

                    if boleto:
                    #     financial_move.date_payment_created = date.today()
                    #     financial_move.transaction_ref = \
                    #         boleto.boleto.format_nosso_numero()
                        financial_move.nosso_numero = nosso_numero

                    boleto_list.append(boleto.boleto)
            except BoletoException as be:
                _logger.error(be.message or be.value, exc_info=True)
                continue
            except Exception as e:
                _logger.error(e.message or e.value, exc_info=True)
                continue
        return boleto_list
