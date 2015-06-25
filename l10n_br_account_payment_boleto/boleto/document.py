# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Payment Boleto module for Odoo
#    Copyright (C) 2012-2015 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo <mileo@kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from datetime import datetime, date
from pyboleto import bank

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class Boleto(object):
    """

    """

    def __init__(self, move_line):
        '''
        Get bank class from bank code.
            '001': 'bancodobrasil.BoletoBB',
            '041': 'banrisul.BoletoBanrisul',
            '237': 'bradesco.BoletoBradesco',
            '104': 'caixa.BoletoCaixa',
            '399': 'hsbc.BoletoHsbc',
            '341': 'itau.BoletoItau',
            '356': 'real.BoletoReal',
            '033': 'santander.BoletoSantander',
        :param bank_code:
        :return:
        '''
        if move_line:
            bank_code = move_line.payment_mode_id.bank_id.bank.bic
            if bank_code in '001':
                self.boleto = bank.get_class_for_codigo(bank_code)(7, 2)
            elif bank_code in '104':
                from pyboleto.bank.caixa_sigcb import BoletoCaixaSigcb

                self.boleto = BoletoCaixaSigcb()
            else:
                self.boleto = bank.get_class_for_codigo(bank_code)
            self.create(move_line)

    def create(self, move_line):
        self.boleto.nosso_numero = move_line.ref.encode('utf-8')
        self.boleto.numero_documento = move_line.name.encode('utf-8')
        self.boleto.data_vencimento = datetime.date(datetime.strptime(
            move_line.date_maturity, '%Y-%m-%d'))
        self.boleto.data_documento = datetime.date(datetime.strptime(
            move_line.invoice.date_invoice, '%Y-%m-%d'))
        self.boleto.data_processamento = date.today()
        self.boleto.valor = str("%.2f" % move_line.debit or move_line.credit)
        self.boleto.valor_documento = str("%.2f" % move_line.debit or
                                move_line.credit)
        self.boleto.especie = \
            move_line.currency_id and move_line.currency_id.symbol or 'R$'
        self.boleto.quantidade = '' #str("%.2f" % move_line.amount_currency)
        self.instrucoes(move_line.payment_mode_id)
        self.payment_mode(move_line.payment_mode_id)
        self.cedente(move_line.company_id)
        self.sacado(move_line.partner_id)


    def instrucoes(self, payment_mode_id):
        """
        :param payment_mode_id:
        :return:
        """
        self.instrucoes = [
            payment_mode_id.instrucoes.encode('utf-8'),
             # move_line.payment_mode_id.instructions_2.encode('utf-8'),
            # move_line.payment_mode_id.instructions_3.encode('utf-8'),
            # move_line.payment_mode_id.instructions_4.encode('utf-8'),
            # move_line.payment_mode_id.instructions_5.encode('utf-8'),
            # move_line.payment_mode_id.instructions_6.encode('utf-8'),
            # move_line.payment_mode_id.instructions_7.encode('utf-8'),
        ]
        # d.demonstrativo = [
        #     move_line.payment_mode_id.demonstrative_1.encode('utf-8'),
        #     move_line.payment_mode_id.demonstrative_2.encode('utf-8'),
        #     move_line.payment_mode_id.demonstrative_3.encode('utf-8'),
        #     move_line.payment_mode_id.demonstrative_4.encode('utf-8'),
        #     move_line.payment_mode_id.demonstrative_5.encode('utf-8'),
        #     move_line.payment_mode_id.demonstrative_6.encode('utf-8'),
        #     move_line.payment_mode_id.demonstrative_7.encode('utf-8'),
        #     move_line.payment_mode_id.demonstrative_8.encode('utf-8'),
        #     move_line.payment_mode_id.demonstrative_9.encode('utf-8'),
        #     move_line.payment_mode_id.demonstrative_10.encode('utf-8'),
        #     move_line.payment_mode_id.demonstrative_11.encode('utf-8'),
        #     move_line.payment_mode_id.demonstrative_12.encode('utf-8'),
        #     move_line.payment_mode_id.demonstrative_13.encode('utf-8'),
        #     move_line.payment_mode_id.demonstrative_14.encode('utf-8'),
        #     move_line.payment_mode_id.demonstrative_15.encode('utf-8'),
        #     ]

    def payment_mode(self, payment_mode_id):
        """
        :param payment_mode:
        :return:
        """
        self.boleto.convenio = payment_mode_id.boleto_convenio.encode('utf-8')
        self.boleto.especie_documento = \
            payment_mode_id.boleto_modalidade.encode('utf-8')
        self.boleto.aceite = payment_mode_id.boleto_aceite
        self.boleto.carteira = payment_mode_id.boleto_carteira.encode('utf-8')
        self.boleto.agencia_cedente = payment_mode_id.bank_id.bra_number.encode('utf-8')
        self.boleto.conta_cedente = str(
            payment_mode_id.bank_id.acc_number + payment_mode_id.bank_id.acc_number_dig).encode('utf-8')
        self.boleto.instrucoes = payment_mode_id.instrucoes

    def cedente(self, company):
        '''

        :param company:
        :return:
        '''
        self.boleto.cedente = company.partner_id.legal_name.encode('utf-8')
        self.boleto.cedente_documento = company.cnpj_cpf.encode('utf-8')
        self.boleto.cedente_bairro = company.district
        self.boleto.cedente_cep = company.zip
        self.boleto.cedente_cidade = company.city
        self.boleto.cedente_endereco = company.street + ', ' + company.number
        self.boleto.cedente_uf = company.state_id.code

    def sacado(self, partner):
        '''

        :param partner:
        :return:
        '''
        self.boleto.sacado = \
            [
                "{0} - CNPJ/CPF: {1}".format(partner.legal_name, partner.cnpj_cpf),
                "{0}, {1}".format(partner.street, partner.number),
            # "{2}".format(fname, lname, age),
            ]
        # self.boleto.sacado_endereco = partner.street + ', ' +
        # self.boleto.sacado_cidade = partner.city
        # self.boleto.sacado_bairro = partner.district
        # self.boleto.sacado_uf = partner.state_id.code
        # self.boleto.sacado_cep = partner.zip
        # self.boleto.sacado_nome = partner.legal_name
        # self.boleto.sacado_documento = partner.cnpj_cpf

    @classmethod
    def get_pdfs(cls, boletoList):
        """

        :param boletoList:
        :return:
        """

        fbuffer = StringIO()

        fbuffer.reset()
        from pyboleto.pdf import BoletoPDF

        boleto = BoletoPDF(fbuffer)
        for i in range(len(boletoList)):
            boleto.drawBoleto(boletoList[i])
            boleto.nextPage()
        boleto.save()
        boleto_file = fbuffer.getvalue()

        fbuffer.close()
        return boleto_file