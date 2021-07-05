# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from .arquivo_certificado import ArquivoCertificado

from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.bank.inter.boleto import BoletoInter
    from erpbrasil.bank.inter.api import ApiInter
except ImportError:
    _logger.error("Biblioteca erpbrasil.bank.inter não instalada")

try:
    from febraban.cnab240.user import User, UserAddress, UserBank
except ImportError:
    _logger.error("Biblioteca febraban não instalada")

try:
    from erpbrasil.base import misc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    def _generate_bank_inter_boleto_data(self):
        dados = []
        myself = User(
            name=self.company_id.legal_name,
            identifier=misc.punctuation_rm(self.company_id.cnpj_cpf),
            bank=UserBank(
                bankId=self.company_partner_bank_id.bank_id.code_bc,
                branchCode=self.company_partner_bank_id.bra_number,
                accountNumber=self.company_partner_bank_id.acc_number,
                accountVerifier=self.company_partner_bank_id.acc_number_dig,
                bankName=self.company_partner_bank_id.bank_id.name,
            ),
        )
        for line in self.bank_line_ids:
            payer = User(
                name=line.partner_id.legal_name,
                identifier=misc.punctuation_rm(
                    line.partner_id.cnpj_cpf
                ),
                email=line.partner_id.email or '',
                personType=(
                    "FISICA" if line.partner_id.company_type == 'person'
                    else 'JURIDICA'),
                phone=misc.punctuation_rm(
                    line.partner_id.phone).replace(" ", ""),
                address=UserAddress(
                    streetLine1=line.partner_id.street or '',
                    district=line.partner_id.district or '',
                    city=line.partner_id.city_id.name or '',
                    stateCode=line.partner_id.state_id.code or '',
                    zipCode=misc.punctuation_rm(line.partner_id.zip),
                    streetNumber=line.partner_id.street_number,
                )
            )
            slip = BoletoInter(
                sender=myself,
                amount=line.amount_currency,
                payer=payer,
                issue_date=line.create_date,
                due_date=line.date,
                identifier=line.name,
                instructions=[
                    'TESTE 1',
                    'TESTE 2',
                    'TESTE 3',
                    'TESTE 4',
                ]
            )
            dados.append(slip)
        return dados

    def _generate_bank_inter_boleto(self):
        with ArquivoCertificado(self.journal_id, 'w') as (key, cert):
            self.api = ApiInter(
                cert=(cert, key),
                conta_corrente=(self.company_partner_bank_id.acc_number +
                                self.company_partner_bank_id.acc_number_dig)
            )
            data = self._generate_bank_inter_boleto_data()
            for item in data:
                resposta = self.api.boleto_inclui(item._emissao_data())
                payment_line_id = self.payment_line_ids.filtered(
                    lambda line: line.bank_line_id.name == item._identifier)
                if payment_line_id:
                    payment_line_id.move_line_id.own_number = \
                        resposta['nossoNumero']
                # bank_line_id.seu_numero = resposta['seuNumero']
                # bank_line_id.linha_digitavel = resposta['linhaDigitavel']
                # bank_line_id.barcode = resposta['codigoBarras']
        return False, False

    def _gererate_bank_inter_api(self):
        """ Realiza a conexão com o a API do banco inter"""
        if self.payment_type == 'inbound':
            return self._generate_bank_inter_boleto()
        else:
            raise NotImplementedError

    @api.multi
    def generate_payment_file(self):
        self.ensure_one()
        try:
            if (self.company_partner_bank_id.bank_id ==
                    self.env.ref('l10n_br_base.res_bank_077') and
                    self.payment_method_id.code == 'electronic'):
                return self._gererate_bank_inter_api()
            else:
                return super().generate_payment_file()
        except Exception as error:
            raise UserError(_(error))
