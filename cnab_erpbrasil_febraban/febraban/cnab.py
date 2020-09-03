# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from __future__ import division, print_function, unicode_literals

import logging
import base64
import codecs

_logger = logging.getLogger(__name__)


try:
    from cnab240.tipos import ArquivoCobranca400
except ImportError as err:
    _logger.debug = (err)


class Cnab(object):

    def __init__(self):
        self.arquivo = False
        self.cnab_type = False

    @staticmethod
    def gerar_remessa(order):
        bank_code = order.company_partner_bank_id.bank_id.code_bc
        cnab_type = order.payment_mode_id.payment_method_id.code

        if cnab_type == '240':
            from febraban.cnab240.itau.sispag import Transfer, File
            from febraban.cnab240.itau.sispag.file.lot import Lot
            from febraban.cnab240.user import User, UserAddress, UserBank
            sender = User(
                name="YOUR COMPANY NAME HERE",
                identifier="12345678901234",
                bank=UserBank(
                    bankId="341",
                    branchCode="4321",
                    accountNumber="12345678",
                    accountVerifier="9"
                ),
                address=UserAddress(
                    streetLine1="AV PAULISTA 1000",
                    city="SAO PAULO",
                    stateCode="SP",
                    zipCode="01310000"
                )
            )

            receiver1 = User(
                name="RECEIVER NAME HERE",
                identifier="01234567890",
                bank=UserBank(
                    bankId="341",
                    branchCode="1234",
                    accountNumber="123456",
                    accountVerifier="9"
                )
            )

            receiver2 = User(
                name="RECEIVER NAME HERE",
                identifier="01234567890",
                bank=UserBank(
                    bankId="341",
                    branchCode="1234",
                    accountNumber="123456",
                    accountVerifier="9"
                )
            )

            receivers = [receiver1, receiver2]

            file = File()
            file.setSender(sender)

            lot = Lot()
            sender.name = "SENDER NAME"
            lot.setSender(sender)
            lot.setHeaderLotType(
                kind="20",  # Tipo de pagamento - Fornecedores
                method="01"  # TED - Outra titularidade
            )

            for receiver in receivers:
                payment = Transfer()
                payment.setSender(sender)
                payment.setReceiver(receiver)
                payment.setAmountInCents("10000")
                payment.setScheduleDate("06052020")
                payment.setInfo(
                    reason="10"  # Crédito em Conta Corrente
                )
                payment.setIdentifier("ID1234567890")
                lot.add(register=payment)

            file.addLot(lot)
            return file.toString().encode()
        elif cnab_type == '400':
            raise NotImplementedError
            # Legacy Code
            from .cnab_400.cnab_400 import Cnab400
            return Cnab400.get_bank(bank)
        elif cnab_type == '500':
            raise NotImplementedError
            # Legacy Code
            from .pag_for.pag_for500 import PagFor500
            return PagFor500.get_bank(bank)
        else:
            return False

    @staticmethod
    def detectar_retorno(cnab_file_object):
        arquivo_retono = base64.b64decode(cnab_file_object)
        f = open('/tmp/cnab_retorno.ret', 'wb')
        f.write(arquivo_retono)
        f.close()
        arquivo_retorno = codecs.open(
            '/tmp/cnab_retorno.ret',
            encoding='ascii'
        )
        header = arquivo_retorno.readline()
        arquivo_retorno.seek(0)

        if 210 < len(header) < 410:
            cnab_type = '400'
            banco = header[76:79]
        elif len(header) < 210:
            cnab_type = '240'
            banco = header[:3]

        cnab = Cnab.get_cnab(banco, cnab_type)()
        return cnab_type, cnab.retorno(arquivo_retorno)

    def retorno(self, arquivo_retorno):
        return ArquivoCobranca400(
            self.classe_retorno,
            arquivo=arquivo_retorno
        )

    def remessa(self, order):
        pass

    def convert_int(self, campo):
        if campo:
            return int(campo)
        # Retornamos de propósito vazio para que a cnab240 acuse o erro do
        # registro em branco pois, se retornarmos ZERO o erro vai passar
        # despercebido
        return ''
