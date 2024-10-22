# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, models
from odoo.exceptions import UserError

from .arquivo_certificado import ArquivoCertificado

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.bank.inter.api import ApiInter
    from erpbrasil.bank.inter.boleto import BoletoInter
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
    _inherit = "account.payment.order"

    def _generate_bank_inter_boleto_data(self):
        dados = []
        myself = User(
            name=self.company_id.legal_name,
            identifier=misc.punctuation_rm(self.company_id.cnpj_cpf),
            bank=UserBank(
                bankId=self.company_partner_bank_id.bank_id.code_bc,
                bankName=self.company_partner_bank_id.bank_id.name,
                accountNumber=self.company_partner_bank_id.acc_number,
                branchCode=self.company_partner_bank_id.bra_number,
                accountVerifier=self.company_partner_bank_id.acc_number_dig,
            ),
            address=UserAddress(
                streetLine1=self.company_id.street or "",
                streetLine2=self.company_id.street_number or "",
                district=self.company_id.district or "",
                city=self.company_id.city_id.name or "",
                stateCode=self.company_id.state_id.code or "",
                zipCode=misc.punctuation_rm(self.company_id.zip),
            ),
        )
        for line in self.payment_line_ids:
            payer = User(
                name=line.partner_id.legal_name,
                identifier=misc.punctuation_rm(line.partner_id.cnpj_cpf),
                address=UserAddress(
                    streetLine1=line.partner_id.street or "",
                    streetLine2=line.partner_id.street_number or "",
                    district=line.partner_id.district or "",
                    city=line.partner_id.city_id.name or "",
                    stateCode=line.partner_id.state_id.code or "",
                    zipCode=misc.punctuation_rm(line.partner_id.zip),
                ),
            )
            slip = BoletoInter(
                sender=myself,
                amount=line.amount_currency,
                payer=payer,
                issue_date=line.create_date,
                due_date=line.date,
                identifier=line.order_id.name,
                instructions=[],
            )
            dados.append(slip)
        return dados

    def _generate_bank_inter_boleto(self):
        with ArquivoCertificado(self.journal_id, "w") as (key, cert):
            api = ApiInter(
                cert=(cert, key),
                conta_corrente=(
                    self.company_partner_bank_id.acc_number
                    + self.company_partner_bank_id.acc_number_dig
                ),
                client_id=self.journal_id.bank_client_id,
                client_secret=self.journal_id.bank_secret_id,
            )
            data = self._generate_bank_inter_boleto_data()
            for item in data:
                resposta = api.boleto_inclui(item._emissao_data())
                payment_line_id = self.payment_line_ids.filtered(
                    lambda line: line.order_id.name == item._identifier
                )
                if payment_line_id:
                    payment_line_id.move_line_id.own_number = resposta["nossoNumero"]
                    payment_line_id.own_number = resposta["nossoNumero"]
        return False, False

    def _gererate_bank_inter_api(self):
        """Realiza a conexão com o a API do banco inter"""
        if self.payment_type == "inbound":
            return self._generate_bank_inter_boleto()
        else:
            raise NotImplementedError

    def generate_payment_file(self):
        self.ensure_one()
        try:
            if (
                self.company_partner_bank_id.bank_id
                == self.env.ref("l10n_br_base.res_bank_077")
                and self.payment_method_id.code == "electronic"
            ):
                return self._gererate_bank_inter_api()
            else:
                return super().generate_payment_file()
        except Exception as error:
            raise UserError(_(error))
