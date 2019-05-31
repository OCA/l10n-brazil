# -*- coding: utf-8 -*-
# © 2019 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from __future__ import division, print_function, unicode_literals

import re
import string
from decimal import Decimal
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm

from ..cnab_400 import Cnab400


class Itau400(Cnab400):

    def __init__(self):
        super(Cnab400, self).__init__()
        from cnab240.bancos import itau_cobranca_400
        self.bank = itau_cobranca_400
        self.controle_linha = 1

    @property
    def inscricao_tipo(self):
        # TODO: Implementar codigo para PIS/PASEP
        if self.order.company_id.partner_id.is_company:
            return 2
        else:
            return 1

    def _prepare_header(self):
        """

        :param order:
        :return:
        """
        vals = {
            'cedente_agencia': int(
                self.order.company_partner_bank_id.bra_number),
            'cedente_conta': int(
                self.order.company_partner_bank_id.acc_number),
            'cedente_conta_dv': int(
                self.order.company_partner_bank_id.acc_number_dig),
            'cedente_nome': unicode(self.order.company_id.legal_name),
            'arquivo_data_de_geracao': self.data_hoje(),
            'arquivo_hora_de_geracao': self.hora_agora(),
            'num_seq_registro':  self.controle_linha,
        }
        self.controle_linha += 1
        return vals

    def _prepare_cobranca(self, line):
        """

        :param line:
        :return:
        """
        sacado_endereco = self.retorna_endereco(line.partner_id.id)

        vals = {
            'identificacao_titulo_empresa': line.identificacao_titulo_empresa,
            'nosso_numero': int(line.nosso_numero),
            'numero_documento': self.adiciona_digitos_num_doc(
                line.numero_documento),
            'cedente_inscricao_tipo': self.inscricao_tipo,
            'cedente_inscricao_numero': int(punctuation_rm(
                self.order.company_id.cnpj_cpf)),
            'cedente_agencia': int(
                self.order.company_partner_bank_id.bra_number),
            'cedente_conta': int(
                self.order.company_partner_bank_id.acc_number),
            'cedente_conta_dv': int(
                self.order.company_partner_bank_id.acc_number_dig
            ),
            'instrucao': 0,  # TODO VERIFICAR
            'quantidade_moeda': 0,
            'carteira_numero': int(
                self.order.payment_mode_id.boleto_carteira
            ),
            'carteira_cod': self.order.payment_mode_id.boleto_modalidade,
            'identificacao_ocorrencia': 1,
            'vencimento_titulo': self.format_date(
                line.date),
            'valor_titulo': Decimal(str(line.amount_currency)).quantize(
                Decimal('1.00')),
            'agencia_cobradora': 0,
            'especie_titulo': self.order.payment_mode_id.boleto_especie,
            'aceite_titulo': self.order.payment_mode_id.boleto_aceite,
            'data_emissao_titulo': self.format_date(
                line.date),  # FIXME
            'primeira_instrucao': int(
                self.order.payment_mode_id.boleto_protesto
            ),
            'segunda_instrucao': int(
                self.order.payment_mode_id.boleto_protesto_prazo

            ),
            'juros_mora_taxa_dia': self.calcula_valor_juros_dia(
                line.amount_currency,
                self.order.payment_mode_id.cnab_percent_interest
            ),
            'data_limite_desconto': 0,
            'valor_desconto': Decimal('0.00'),
            'valor_iof': Decimal('0.00'),
            'valor_abatimento': Decimal('0.00'),
            'sacado_inscricao_tipo': int(
                self.sacado_inscricao_tipo(line.partner_id)),
            'sacado_inscricao_numero': int(
                self.rmchar(line.partner_id.cnpj_cpf)),
            'sacado_nome': line.partner_id.legal_name,
            'sacado_endereco': sacado_endereco,
            'sacado_bairro': line.partner_id.district or '',
            'sacado_cep': int(line.partner_id.zip.replace('-', '')),
            'sacado_cidade': line.partner_id.l10n_br_city_id.name,
            'sacado_uf': line.partner_id.state_id.code,
            'sacador_avalista': self.order.payment_mode_id.comunicacao_2,
            'juros_mora_data': 0,
            # self.format_date(
            # line.date),
            'prazo': 0,  # De 5 a 120 dias.
            # 'sacador_avalista': u'Protestar após 5 dias',
            'num_seq_registro': self.controle_linha,
        }
        self.controle_linha += 1
        return vals

    def nosso_numero(self, format):
        digito = format[-1:]
        carteira = format[:3]
        nosso_numero = re.sub(
            '[%s]' % re.escape(string.punctuation), '', format[3:-1] or '')
        return carteira, nosso_numero, digito

    def retorna_id_empr_benef(self):
        dig_cart = 3
        dig_ag = 5
        dig_conta = 7

        carteira = self.adiciona_digitos(
            self.order.payment_mode_id.boleto_carteira, dig_cart)
        agencia = self.adiciona_digitos(
            self.order.company_partner_bank_id.bra_number, dig_ag)
        conta = self.adiciona_digitos(
            self.order.company_partner_bank_id.acc_number, dig_conta)

        ident = u'0' + (carteira) + (agencia) + (conta) + \
                (self.order.company_partner_bank_id.acc_number_dig)
        return ident

    def adiciona_digitos(self, campo, num_digitos):
        chars_faltantes = num_digitos - len(campo)
        return (u'0' * chars_faltantes) + campo


def str_to_unicode(inp_str):
    inp_str = unicode(inp_str, "utf-8")
    return inp_str
