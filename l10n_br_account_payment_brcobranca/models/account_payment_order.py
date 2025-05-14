# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# Copyright 2020 KMEE
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging
import tempfile

import requests
from erpbrasil.base import misc

from odoo import _, models
from odoo.exceptions import ValidationError

from ..constants.br_cobranca import (
    DICT_BRCOBRANCA_CNAB_TYPE,
    TIMEOUT,
    get_brcobranca_api_url,
    get_brcobranca_bank,
)

_logger = logging.getLogger(__name__)


class PaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def _prepare_remessa_banco_brasil(self, remessa_values, cnab_config):
        remessa_values.update(
            {
                "convenio": int(cnab_config.cnab_company_bank_code),
                "carteira": str(cnab_config.boleto_wallet).zfill(2),
            }
        )

        if cnab_config.payment_method_code == "240":
            remessa_values.update(
                {
                    "variacao": cnab_config.boleto_variation.zfill(3),
                }
            )

        if cnab_config.payment_method_code == "400":
            remessa_values.update(
                {
                    "variacao_carteira": cnab_config.boleto_variation.zfill(3),
                    "convenio_lider": cnab_config.convention_code.zfill(7),
                }
            )

    def _prepare_remessa_santander(self, remessa_values, cnab_config):
        remessa_values.update(
            {
                "codigo_carteira": cnab_config.wallet_code_id.code,
                "codigo_transmissao": cnab_config.cnab_company_bank_code,
                "conta_corrente": misc.punctuation_rm(
                    self.journal_id.bank_account_id.acc_number
                ),
            }
        )

    def _prepare_remessa_caixa(self, remessa_values, cnab_config):
        remessa_values.update(
            {
                "convenio": int(cnab_config.cnab_company_bank_code),
                "digito_agencia": self.journal_id.bank_account_id.bra_number_dig,
            }
        )

    def _prepare_remessa_ailos(self, remessa_values, cnab_config):
        remessa_values.update(
            {
                "convenio": int(cnab_config.cnab_company_bank_code),
                "digito_agencia": self.journal_id.bank_account_id.bra_number_dig,
            }
        )

    def _prepare_remessa_unicred(self, remessa_values, cnab_config):
        remessa_values["codigo_beneficiario"] = int(cnab_config.cnab_company_bank_code)

    def _prepare_remessa_sicredi(self, remessa_values, cnab_config):
        bank_account_id = self.journal_id.bank_account_id
        remessa_values.update(
            {
                # Aparentemente a validação do BRCobranca nesse caso gera erro
                # quando é feito o int(misc.punctuation_rm(bank_account_id.acc_number))
                "conta_corrente": misc.punctuation_rm(bank_account_id.acc_number),
                "posto": cnab_config.boleto_post,
                "byte_idt": cnab_config.boleto_byte_idt,
            }
        )

    def _prepare_remessa_bradesco(self, remessa_values, cnab_config):
        remessa_values["codigo_empresa"] = int(cnab_config.cnab_company_bank_code)

    def generate_payment_file(self):
        """Returns (payment file as string, filename)"""
        self.ensure_one()
        cnab_config = self.payment_mode_id.cnab_config_id
        self.file_number = cnab_config.cnab_sequence_id.next_by_id()

        # see remessa fields here:
        # https://github.com/kivanio/brcobranca/blob/master/lib/brcobranca/remessa/base.rb
        # https://github.com/kivanio/brcobranca/tree/master/lib/brcobranca/remessa/cnab240
        # https://github.com/kivanio/brcobranca/tree/master/lib/brcobranca/remessa/cnab400
        # and a test here:
        # https://github.com/kivanio/brcobranca/blob/master/spec/
        # brcobranca/remessa/cnab400/itau_spec.rb

        cnab_type = cnab_config.payment_method_id.code

        # Se não for um caso CNAB deve chamar o super
        if (
            cnab_type not in ("240", "400", "500")
            or cnab_config.cnab_processor != "brcobranca"
        ):
            return super().generate_payment_file()

        bank_account_id = self.journal_id.bank_account_id
        bank_brcobranca = get_brcobranca_bank(bank_account_id, cnab_type)

        # Verificar campos que não podem ser usados no CNAB, já é
        # feito ao criar um Modo de Pagamento, porém para evitar
        # erros devido alterações e re-validado aqui
        cnab_config._check_cnab_restriction()

        if cnab_type not in bank_brcobranca.remessa:
            # Informa se o CNAB especifico de um Banco não está implementado
            # no BRCobranca, evitando a mensagem de erro mais extensa da lib
            raise ValidationError(
                _(
                    "The CNAB %(cnab_type)s for Bank %(bank_name)s are not implemented "
                    "in BRCobranca.",
                    cnab_type=cnab_type,
                    bank_name=bank_account_id.bank_id.name,
                )
            )

        pagamentos = []
        for line in self.payment_line_ids:
            pagamentos.append(line.prepare_bank_payment_line(bank_brcobranca))

        remessa_values = {
            "carteira": str(cnab_config.boleto_wallet),
            "agencia": bank_account_id.bra_number,
            "conta_corrente": int(misc.punctuation_rm(bank_account_id.acc_number)),
            "digito_conta": bank_account_id.acc_number_dig[0],
            "empresa_mae": bank_account_id.partner_id.legal_name[:30],
            "documento_cedente": misc.punctuation_rm(
                bank_account_id.partner_id.cnpj_cpf
            ),
            "pagamentos": pagamentos,
            "sequencial_remessa": self.file_number,
        }

        # Casos onde o Banco além dos principais campos possui campos
        # específicos, dos casos por enquanto mapeados, se estiver vendo
        # um caso que está faltando por favor considere fazer um
        # PR para ajudar
        if hasattr(self, f"_prepare_remessa_{bank_brcobranca.name}"):
            bank_method = getattr(self, f"_prepare_remessa_{bank_brcobranca.name}")
            bank_method(remessa_values, cnab_config)

        remessa = self._get_brcobranca_remessa(
            bank_brcobranca, remessa_values, cnab_type
        )

        return remessa, self.get_file_name(cnab_type)

    def _get_brcobranca_remessa(self, bank_brcobranca, remessa_values, cnab_type):
        content = json.dumps(remessa_values)
        f = open(tempfile.mktemp(), "w")
        f.write(content)
        f.close()
        files = {"data": open(f.name, "rb")}

        brcobranca_api_url = get_brcobranca_api_url(self.env)
        # EX.: "http://boleto_cnab_api:9292/api/remessa"
        brcobranca_service_url = brcobranca_api_url + "/api/remessa"
        _logger.info(
            "Connecting to %s to generate CNAB-REMESSA file for Payment Order %s",
            brcobranca_service_url,
            self.name,
        )
        res = requests.post(
            brcobranca_service_url,
            data={
                "type": DICT_BRCOBRANCA_CNAB_TYPE[cnab_type],
                "bank": bank_brcobranca.name,
            },
            files=files,
            timeout=TIMEOUT,
        )

        if cnab_type == "240" and "R01" in res.text[242:254]:
            #  Todos os header de lote cnab 240 tem conteúdo: R01,
            #  verificar observações G025 e G028 do manual cnab 240 febraban.
            remessa = res.content
        elif cnab_type == "400" and res.text[:3] in ("01R", "DCB"):
            # A remessa 400 não tem um layout padronizado,
            # entretanto a maiorias dos arquivos começa com 01REMESSA,
            # o banco de brasilia começa com DCB...
            # Dúvidas verificar exemplos:
            # https://github.com/kivanio/brcobranca/tree/master/spec/fixtures/remessa
            remessa = res.content
        else:
            raise ValidationError(res.text)

        return remessa

    def generated2uploaded(self):
        result = super().generated2uploaded()
        for payment_line in self.payment_line_ids:
            # No caso de Cancelamento da Invoice a AML é apagada
            if payment_line.move_line_id:
                # Importante para saber a situação do CNAB no caso
                # de um pagto feito por fora ( dinheiro, deposito, etc)
                payment_line.move_line_id.cnab_state = "exported"
        return result
