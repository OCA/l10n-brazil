# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models, _

from pybrasil.base import modulo11, modulo10

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
        size=54,
    )
    boleto_codigo_barras = fields.Char(
        string='Código de barras',
        size=44,
    )

    @api.multi
    @api.depends('boleto_codigo_barras')
    def compute_codigo_barras(self):
        '''
        Posição  #   Conteúdo
        01 a 03  03  Número do banco
        04       01  Código da Moeda - 9 para Real
        05       01  Digito verificador do Código de Barras
        06 a 09  04  Data de vencimento em dias partis de 07/10/1997
        10 a 19  10  Valor do boleto (8 inteiros e 2 decimais)
        20 a 44  25  Campo Livre definido por cada banco
        Total    44
        '''

        for move in self:
            if not move.boleto_codigo_barras:
                continue

            if len(move.boleto_codigo_barras) != 44:
                pass
                # raise

            dv = move.boleto_codigo_barras[4]
            codigo_barras = move.boleto_codigo_barras[0:4] + \
                            move.boleto_codigo_barras[5:]

            dv_calculado = modulo11(codigo_barras,
                                    mapa_digitos={0: 1, 1: 1, 10: 1, 11: 1})

            if dv_calculado != dv:
                pass
                # raise

            # valor = move.boleto_codigo_barras[9:17] + '.' + \
            #     move.boleto_codigo_barras[17:19]
            # valor = float(valor)
            # data_vencimento = move.boleto_codigo_barras[5:9]

            #
            # Monta a linha digitável
            #
            campo_1 = move.boleto_codigo_barras[0:4] + \
                      move.boleto_codigo_barras[19:24]
            campo_2 = move.boleto_codigo_barras[24:34]
            campo_3 = move.boleto_codigo_barras[34:44]
            campo_4 = move.boleto_codigo_barras[4]
            campo_5 = move.boleto_codigo_barras[5:19]

            #
            # Dígitos verificadores
            #
            campo_1 += str(modulo10(campo_1, modulo=False))
            campo_2 += str(modulo10(campo_2, modulo=False))
            campo_3 += str(modulo10(campo_3, modulo=False))

            campo_1 = campo_1[:5] + '.' + campo_1[5:]
            campo_2 = campo_2[:5] + '.' + campo_2[5:]
            campo_3 = campo_3[:5] + '.' + campo_3[5:]

            move.boleto_linha_digitavel = ' '.join([campo_1, campo_2, campo_3,
                                                    campo_4, campo_5])

    @api.multi
    def gera_boleto(self):

        print ('Chegou AQUI!')

        boleto_list = []

        for move_line in self:
            try:

                if True:
                # if move_line.payment_mode_id.type_payment == '00':
                #     number_type = move_line.company_id.own_number_type
                #     if not move_line.boleto_own_number:
                #         if number_type == '0':
                #             nosso_numero = self.env['ir.sequence'].next_by_id(
                #                 move_line.company_id.own_number_sequence.id)
                #         elif number_type == '1':
                #             nosso_numero = \
                #                 move_line.transaction_ref.replace('/', '')
                #         else:
                #             nosso_numero = self.env['ir.sequence'].next_by_id(
                #                 move_line.payment_mode_id.
                #                 internal_sequence_id.id)
                #     else:
                #         nosso_numero = move_line.boleto_own_number
                    nosso_numero = move_line.nosso_numero
                    nosso_numero = 3751

                    boleto = Boleto.getBoleto(move_line, nosso_numero)

                    if boleto:
                        move_line.date_payment_created = date.today()
                        move_line.transaction_ref = \
                            boleto.boleto.format_nosso_numero()
                        move_line.boleto_own_number = nosso_numero

                    boleto_list.append(boleto.boleto)
            except BoletoException as be:
                _logger.error(be.message or be.value, exc_info=True)
                continue
            except Exception as e:
                _logger.error(e.message or e.value, exc_info=True)
                continue
        return boleto_list