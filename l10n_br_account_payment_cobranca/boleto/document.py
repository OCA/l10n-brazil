# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA (Luis Felipe Mileo mileo@kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, date
import logging

_logger = logging.getLogger(__name__)

try:
    from pyboleto import bank
except ImportError as err:
    _logger.debug = err

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
BoletoException = bank.BoletoException


class Boleto:
    boleto = object
    account_number = ''
    account_digit = ''

    branch_number = ''
    branch_digit = ''

    nosso_numero = ''

    @staticmethod
    def getBoleto(move_line, nosso_numero):
        boleto_type = move_line.payment_mode_id.boleto_type
        if boleto_type:
            return dict_boleto[boleto_type][0](move_line, nosso_numero)
        raise BoletoException(u'Configure o tipo de boleto no modo de '
                              u'pagamento')

    @staticmethod
    def getBoletoClass(move_line):
        bank_code = move_line.payment_mode_id.bank_id.bank.bic
        return bank.get_class_for_codigo(bank_code)

    def __init__(self, move_line, nosso_numero):
        self._cedente(move_line.company_id)
        self._sacado(move_line.partner_id)
        self._move_line(move_line)
        self.nosso_numero = str(nosso_numero)

    def getAccountNumber(self):
        if self.account_digit:
            return str(self.account_number + '-' +
                       self.account_digit).encode('utf-8')
        return self.account_number.encode('utf-8')

    def getBranchNumber(self):
        if self.branch_digit:
            return str(self.branch_number + '-' +
                       self.branch_digit).encode('utf-8')
        return self.branch_number.encode('utf-8')

    def _move_line(self, move_line):
        self._payment_mode(move_line.payment_mode_id)
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
        self.boleto.quantidade = ''  # str("%.2f" % move_line.amount_currency)
        self.boleto.numero_documento = move_line.name.encode('utf-8')

    def _payment_mode(self, payment_mode_id):
        """
        :param payment_mode:
        :return:
        """
        self.boleto.convenio = payment_mode_id.boleto_convenio
        self.boleto.especie_documento = payment_mode_id.boleto_modalidade
        self.boleto.aceite = payment_mode_id.boleto_aceite
        self.boleto.carteira = str(payment_mode_id.boleto_carteira)

    def _cedente(self, company):
        """
        :param company:
        :return:
        """
        self.boleto.cedente = company.partner_id.legal_name.encode('utf-8')
        self.boleto.cedente_documento = company.cnpj_cpf.encode('utf-8')
        self.boleto.cedente_bairro = company.district
        self.boleto.cedente_cep = company.zip
        self.boleto.cedente_cidade = company.city
        self.boleto.cedente_logradouro = company.street + ', ' + company.number
        self.boleto.cedente_uf = company.state_id.code
        self.boleto.agencia_cedente = self.getBranchNumber()
        self.boleto.conta_cedente = self.getAccountNumber()

    def _sacado(self, partner):
        """

        :param partner:
        :return:
        """
        self.boleto.sacado_endereco = partner.street + ', ' + partner.number
        self.boleto.sacado_cidade = partner.city
        self.boleto.sacado_bairro = partner.district
        self.boleto.sacado_uf = partner.state_id.code
        self.boleto.sacado_cep = partner.zip
        self.boleto.sacado_nome = partner.legal_name
        self.boleto.sacado_documento = partner.cnpj_cpf

    @classmethod
    def get_pdfs(cls, boleto_list):
        """

        :param boletoList:
        :return:
        """
        fbuffer = StringIO()

        fbuffer.reset()
        from pyboleto.pdf import BoletoPDF

        boleto = BoletoPDF(fbuffer)
        for i in range(len(boleto_list)):
            boleto.drawBoleto(boleto_list[i])
            boleto.nextPage()
        boleto.save()
        boleto_file = fbuffer.getvalue()

        fbuffer.close()
        return boleto_file


class BoletoBB(Boleto):

    def __init__(self, move_line, nosso_numero):
        # TODO: size o convenio and nosso numero, replace (7,2)
        # Size of convenio 4, 6, 7 or 8
        # Nosso Numero format. 1 or 2
        # Used only for convenio=6
        # 1: Nosso Numero with 5 positions
        # 2: Nosso Numero with 17 positions
        self.boleto = Boleto.getBoletoClass(move_line)(7, 2)
        self.account_number = move_line.payment_mode_id.bank_id.acc_number
        self.branch_number = move_line.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


class BoletoBarisul(Boleto):

    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = move_line.payment_mode_id.bank_id.acc_number
        self.branch_number = move_line.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


class BoletoBradesco(Boleto):

    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = move_line.payment_mode_id.bank_id.acc_number
        self.branch_number = move_line.payment_mode_id.bank_id.bra_number
        # bank specific
        self.account_digit = move_line.payment_mode_id.bank_id.acc_number_dig
        self.branch_digit = move_line.payment_mode_id.bank_id.bra_number_dig
        # end bank specific
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


class BoletoCaixa(Boleto):

    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = move_line.payment_mode_id.bank_id.acc_number
        self.branch_number = move_line.payment_mode_id.bank_id.bra_number
        # bank specific
        self.account_digit = move_line.payment_mode_id.bank_id.acc_number_dig
        # end bank specific
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


class BoletoHsbc(Boleto):

    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = move_line.payment_mode_id.bank_id.acc_number
        self.branch_number = move_line.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


class BoletoItau157(Boleto):

    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = move_line.payment_mode_id.bank_id.acc_number
        self.branch_number = move_line.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


class BoletoItau(Boleto):

    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = move_line.payment_mode_id.bank_id.acc_number
        self.branch_number = move_line.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


class BoletoReal(Boleto):

    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = move_line.payment_mode_id.bank_id.acc_number
        self.branch_number = move_line.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


class BoletoSantander101(Boleto):

    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = move_line.payment_mode_id.bank_id.acc_number
        self.branch_number = move_line.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.ios = '0'
        self.boleto.nosso_numero = self.nosso_numero


class BoletoStatander101201(Boleto):

    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = move_line.payment_mode_id.bank_id.acc_number
        self.branch_number = move_line.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.ios = '0'
        self.boleto.nosso_numero = self.nosso_numero


class BoletoCaixaSigcb(Boleto):

    def __init__(self, move_line, nosso_numero):
        from pyboleto.bank.caixa_sigcb import BoletoCaixaSigcb
        self.boleto = BoletoCaixaSigcb()
        self.account_number = move_line.payment_mode_id.bank_id.acc_number
        self.branch_number = move_line.payment_mode_id.bank_id.bra_number
        # bank specific
        self.account_digit = move_line.payment_mode_id.bank_id.acc_number_dig
        # end bank specific
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


class BoletoSicredi(Boleto):

    def __init__(self, move_line, nosso_numero):
        self.boleto = Boleto.getBoletoClass(move_line)()
        self.account_number = move_line.payment_mode_id.bank_id.acc_number
        self.branch_number = move_line.payment_mode_id.bank_id.bra_number
        Boleto.__init__(self, move_line, nosso_numero)
        self.boleto.nosso_numero = self.nosso_numero


dict_boleto = {
    '1': (BoletoBB, 'Banco do Brasil 18'),
    '2': (BoletoBarisul, 'Barisul x'),
    '3': (BoletoBradesco, 'Bradesco 06, 03'),
    '4': (BoletoCaixa, 'Caixa Economica SR'),
    '5': (BoletoHsbc, 'HSBC CNR CSB'),
    '6': (BoletoItau157, 'Itau 157'),
    '7': (BoletoItau, 'Itau 175, 174, 178, 104, 109'),
    '8': (BoletoReal, 'Real 57'),
    '9': (BoletoSantander101, 'Santander 102'),
    '10': (BoletoStatander101201, 'Santander 101, 201'),
    '11': (BoletoCaixaSigcb, 'Caixa Sigcb'),
    '12': (BoletoSicredi, 'Sicredi'),
}


def getBoletoSelection():
    list = []
    for i in dict_boleto:
        list.append((i, dict_boleto[i][1]))
    return list
