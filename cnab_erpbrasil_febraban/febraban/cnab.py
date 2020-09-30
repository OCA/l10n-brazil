# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import base64
import codecs
from unidecode import unidecode

_logger = logging.getLogger(__name__)

try:
    from febraban.cnab240.itau.sispag import \
        Transfer, DasPayment, IssPayment, UtilityPayment, File
    from febraban.cnab240.itau.sispag.file.lot import Lot
    from febraban.cnab240.libs.barCode import LineNumberO
    from febraban.cnab240.user import User, UserAddress, UserBank
except ImportError as err:
    _logger.debug = (err)


class Cnab(object):

    def __init__(self):
        self.arquivo = False
        self.cnab_type = False

    @staticmethod
    def gerar_remessa(order):
        bank_id = order.company_partner_bank_id.bank_id
        bank_code = bank_id.code_bc
        cnab_type = order.payment_mode_id.payment_method_id.code

        if cnab_type == '240':
            sender = User(
                name=order.company_id.legal_name.upper(),
                identifier=order.company_id.cnpj_cpf.replace(
                    '.', '').replace('/', '').replace('-', ''),
                bank=UserBank(
                    bankId=bank_code,
                    branchCode=order.company_partner_bank_id.bra_number,
                    accountNumber=order.company_partner_bank_id.acc_number,
                    accountVerifier=
                    order.company_partner_bank_id.acc_number_dig
                ),
                address=UserAddress(
                    streetLine1=(order.company_id.partner_id.street + ' ' +
                                 (order.company_id.partner_id.street_number
                                  or '')).upper(),
                    city=unidecode(order.company_id.city_id.name).upper(),
                    stateCode=order.company_id.state_id.code,
                    zipCode=order.company_id.zip.replace('-', '')
                )
            )

            bank_line_obj = order.env['bank.payment.line']
            option_obj = order.env['l10n_br.cnab.option']

            file = File()
            file.setSender(sender)

            for group in bank_line_obj.read_group(
                [('id', 'in', order.bank_line_ids.ids)],
                [], ['release_form_id', 'service_type_id'], lazy=False
            ):
                lot = Lot()
                sender.name = order.company_id.legal_name.upper()
                lot.setSender(sender)
                lot.setHeaderLotType(
                    kind=option_obj.browse(group['service_type_id'][0]).code,
                    method=option_obj.browse(group['release_form_id'][0]).code,
                )

                for line in bank_line_obj.search(group['__domain']):
                    receiver = User(
                        name=line.partner_id.name.upper(),
                        identifier=(line.partner_id.cnpj_cpf or ''
                                    ).replace('-', '').replace(
                            '.', '').replace('/', ''),
                        bank=UserBank(
                            bankId=line.partner_bank_id.bank_id.code_bc,
                            branchCode=line.partner_bank_id.bra_number,
                            accountNumber=line.partner_bank_id.acc_number,
                            accountVerifier=
                            line.partner_bank_id.acc_number_dig
                        )
                    )

                    if line.release_form_id.code == "41":
                        payment = Transfer()
                        payment.setSender(sender)
                        payment.setReceiver(receiver)
                        payment.setAmountInCents(str(int(line.amount_currency * 100)))
                        payment.setScheduleDate(line.date.strftime('%d%m%Y'))
                        payment.setInfo(
                            reason="10"  # Crédito em Conta Corrente
                        )
                        payment.setIdentifier("ID%s" % line.own_number)
                    elif line.release_form_id.code == "91":
                        payment = DasPayment()
                        payment.setPayment(
                            sender=sender,
                            scheduleDate=line.date.strftime('%d%m%Y'),
                            identifier="ID%s" % line.own_number,
                            lineNumber=LineNumberO(line.communication)
                        )
                    elif line.release_form_id.code == "19":
                        payment = IssPayment()
                        payment.setPayment(
                            sender=sender,
                            scheduleDate=line.date.strftime('%d%m%Y'),
                            identifier="ID%s" % line.own_number,
                            lineNumber=LineNumberO(line.communication)
                        )
                    elif line.release_form_id.code == "13":
                        payment = UtilityPayment()
                        payment.setPayment(
                            sender=sender,
                            scheduleDate=line.date.strftime('%d%m%Y'),
                            identifier="ID%s" % line.own_number,
                            lineNumber=LineNumberO(line.communication)
                        )
                    else:
                        continue
                    lot.add(register=payment)

                file.addLot(lot)

            return file.toString().encode()

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
    #
    # def retorno(self, arquivo_retorno):
    #     return ArquivoCobranca400(
    #         self.classe_retorno,
    #         arquivo=arquivo_retorno
    #     )
