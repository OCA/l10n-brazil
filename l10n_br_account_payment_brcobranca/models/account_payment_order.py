# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# Copyright 2020 KMEE
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json
import logging
import tempfile

import requests
from erpbrasil.base import misc

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from ..constants.br_cobranca import (
    DICT_BRCOBRANCA_CNAB_TYPE,
    TIMEOUT,
    get_brcobranca_api_url,
    get_brcobranca_bank,
)

_logger = logging.getLogger(__name__)

# Manual Sicredi CNAB 240 - item 6.2 (Codificação dos meses).
# Janeiro a Setembro são números, Outubro, Novembro e Dezembro usam letras.
DICT_SICREDI_MONTH_CODE = {
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "O",
    11: "N",
    12: "D",
}


class PaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def _prepare_remessa_banco_brasil(self, remessa_values, cnab_config):
        remessa_values.update(
            {
                "convenio": str(cnab_config.cnab_company_bank_code),
                "carteira": str(cnab_config.boleto_wallet).zfill(2),
            }
        )

        if cnab_config.payment_method_code == "240":
            remessa_values.update(
                {
                    "variacao": cnab_config.boleto_variation.zfill(3),
                    "agencia": str(self.journal_id.bank_account_id.bra_number),
                    "conta_corrente": str(
                        misc.punctuation_rm(self.journal_id.bank_account_id.acc_number)
                    ),
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
                # Manual Sicredi CNAB 240 -posição 20 do código de barras:
                # "1" – Com Registro, "3" – Sem Registro.
                # O boleto deve ser "Com Registro" (1) para aptidão ao pagamento.
                "carteira": "1",
                # Aparentemente a validação do BRCobranca nesse caso gera erro
                # quando é feito o int(misc.punctuation_rm(bank_account_id.acc_number))
                "conta_corrente": misc.punctuation_rm(bank_account_id.acc_number),
                "posto": cnab_config.boleto_post,
                "byte_idt": cnab_config.boleto_byte_idt,
            }
        )

    def _prepare_remessa_bradesco(self, remessa_values, cnab_config):
        remessa_values["codigo_empresa"] = int(cnab_config.cnab_company_bank_code)

    def _build_remessa_values(self, sequencial):
        cnab_config = self.payment_mode_id.cnab_config_id
        bank_account_id = self.journal_id.bank_account_id
        bank_brcobranca = get_brcobranca_bank(
            bank_account_id, cnab_config.payment_method_id.code
        )
        pagamentos = []
        for line in self.payment_line_ids:
            pagamentos.append(line.prepare_bank_payment_line(bank_brcobranca))

        # O Cedente da Remessa é a Empresa da Ordem de Pagamento, o Parceiro
        # da Conta Bancária é usado apenas como Fallback porque pode ser um
        # parceiro sem o CNPJ/CPF preenchido mesmo com os dados da Empresa
        # preenchidos, isso está de acordo com o que é feito na geração do
        # Boleto em l10n_br_account_payment_brcobranca/models/account_move_line.py
        cedente = bank_account_id.partner_id
        if self.company_id and self.company_id.cnpj_cpf:
            cedente = self.company_id.partner_id

        if not cedente.cnpj_cpf:
            raise ValidationError(
                _(
                    "Missing CNPJ/CPF of the Cedente. Please fill the "
                    "CNPJ/CPF of the Company '%(company)s' or of the holder "
                    "'%(holder)s' of the bank account '%(bank)s'.",
                    company=self.company_id.name,
                    holder=cedente.name,
                    bank=bank_account_id.display_name,
                )
            )

        remessa_values = {
            "carteira": str(cnab_config.boleto_wallet),
            "agencia": bank_account_id.bra_number,
            "conta_corrente": int(misc.punctuation_rm(bank_account_id.acc_number)),
            "digito_conta": bank_account_id.acc_number_dig[0],
            "empresa_mae": (cedente.legal_name or cedente.name)[:30],
            "documento_cedente": misc.punctuation_rm(cedente.cnpj_cpf),
            "pagamentos": pagamentos,
            "sequencial_remessa": sequencial,
        }

        # Casos onde o Banco além dos principais campos possui campos
        # específicos, dos casos por enquanto mapeados, se estiver vendo
        # um caso que está faltando por favor considere fazer um
        # PR para ajudar
        if hasattr(self, f"_prepare_remessa_{bank_brcobranca.name}"):
            bank_method = getattr(self, f"_prepare_remessa_{bank_brcobranca.name}")
            bank_method(remessa_values, cnab_config)

        return remessa_values, bank_brcobranca, cnab_config

    def _get_file_number(self):
        """Próximo número sequencial a ser usado no arquivo.

        Na geração o file_number é um placeholder (0) e a sequência só é
        consumida na confirmação de envio. Retorna o próximo número da
        sequência sem consumí-lo, para que o nome do arquivo e o header do
        CNAB já reflitam o valor real (ex.: 8 -> extensão .008 e sequencial
        do header 000008).
        """
        file_number = self.file_number
        if not file_number:
            cnab_config = self.payment_mode_id.cnab_config_id
            if cnab_config and cnab_config.cnab_sequence_id:
                file_number = int(cnab_config.cnab_sequence_id.number_next_actual)
        return file_number

    def generate_payment_file(self):
        """Returns (payment file as string, filename)"""
        self.ensure_one()
        cnab_config = self.payment_mode_id.cnab_config_id

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

        # A sequencia sera consumida apenas na confirmacao de envio
        # (generated2uploaded) para evitar gaps e permitir que o usuario
        # edite o numero antes de confirmar. Aqui usamos 0 como placeholder,
        # mas o nome do arquivo e o sequencial do header usam o proximo
        # numero da sequencia (sem consumir).
        self.file_number = 0

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

        remessa_values, bank_brcobranca, cnab_config = self._build_remessa_values(
            self._get_file_number()
        )
        remessa = self._get_brcobranca_remessa(
            bank_brcobranca, remessa_values, cnab_type
        )

        return remessa, self.get_file_name(cnab_type)

    def get_file_name(self, cnab_type):
        bank_account_id = self.journal_id.bank_account_id
        if bank_account_id.bank_id.code_bc == "748":
            # Manual Sicredi CNAB 240 - item 6.1 (Nomenclatura dos arquivos).
            # Arquivo de remessa no formato CCCCCMDD.XXX:
            # CCCCC = Código do beneficiário (Conta Corrente), MDD = Código
            # do mês e nº do dia da data de geração do arquivo e XXX =
            # extensão de uso livre que não pode se repetir durante o dia,
            # o manual sugere 001, 002, etc.
            context_today = fields.Date.context_today(self)
            file_number = self._get_file_number()
            month_code = DICT_SICREDI_MONTH_CODE[context_today.month]
            day = context_today.strftime("%d")
            codigo_beneficiario = misc.punctuation_rm(
                bank_account_id.acc_number
            ).zfill(5)
            return f"{codigo_beneficiario}{month_code}{day}.{file_number:03d}"
        return super().get_file_name(cnab_type)

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

        # O BRCobranca (API Ruby) grava no header a data de geração usando
        # o fuso do servidor da API, que pode ser diferente do fuso do
        # usuário do Odoo, fazendo a data do arquivo (ex.: nome do arquivo
        # e data de processamento) não conferir com o header, caso do
        # Manual Sicredi CNAB 240 itens 6.1 (Nomenclatura dos arquivos) e
        # 6.4 (Data de Geração do Arquivo).
        remessa = self._fix_remessa_header_date(remessa, cnab_type)

        return remessa

    def _fix_remessa_header_date(self, remessa, cnab_type):
        """Corrige a data de geração do header do arquivo CNAB 240.

        A API BRCobranca preenche o campo 'Data de Geração do Arquivo'
        (posições 144-151 do registro header) com a data do fuso do
        servidor onde ela roda, que pode divergir da data do usuário do
        Odoo usada no nome do arquivo (Manual Sicredi CNAB 240 - item 6.1)
        e na data de processamento, fazendo o banco rejeitar o arquivo.
        """
        if cnab_type != "240" or not remessa:
            return remessa
        context_today = fields.Date.context_today(self)
        header_date = context_today.strftime("%d%m%Y").encode()
        if len(remessa) >= 151:
            # Registro header do arquivo é a primeira linha do CNAB 240,
            # com a data de geração nas posições 144-151 (1-based).
            remessa = remessa[:143] + header_date + remessa[151:]
        return remessa

    def _regenerate_cnab_attachment(self):
        """Regenerate the CNAB file with the current file_number and update
        the attachment."""
        cnab_config = self.payment_mode_id.cnab_config_id
        cnab_type = cnab_config.payment_method_id.code
        remessa_values, bank_brcobranca, cnab_config = self._build_remessa_values(
            self._get_file_number()
        )
        remessa = self._get_brcobranca_remessa(
            bank_brcobranca, remessa_values, cnab_type
        )
        new_filename = self.get_file_name(cnab_type)
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "account.payment.order"),
                ("res_id", "=", self.id),
            ],
            order="create_date desc",
            limit=1,
        )
        if attachment:
            attachment.write(
                {
                    "datas": base64.b64encode(remessa),
                    "name": new_filename,
                }
            )
        self.cnab_file = base64.b64encode(remessa)
        self.cnab_filename = new_filename

    def write(self, vals):
        result = super().write(vals)
        if "file_number" in vals:
            for record in self:
                cnab_config = record.payment_mode_id.cnab_config_id
                if (
                    cnab_config
                    and cnab_config.cnab_processor == "brcobranca"
                    and record.state == "generated"
                    and vals.get("file_number")
                ):
                    record._regenerate_cnab_attachment()
        return result

    def generated2uploaded(self):
        cnab_config = self.payment_mode_id.cnab_config_id
        if (
            cnab_config
            and cnab_config.cnab_processor == "brcobranca"
            and cnab_config.cnab_sequence_id
        ):
            if not self.file_number:
                self.file_number = cnab_config.cnab_sequence_id.next_by_id()

            self._regenerate_cnab_attachment()

        result = super().generated2uploaded()
        for payment_line in self.payment_line_ids:
            # No caso de Cancelamento da Invoice a AML é apagada
            if payment_line.move_line_id:
                # Importante para saber a situação do CNAB no caso
                # de um pagto feito por fora ( dinheiro, deposito, etc)
                payment_line.move_line_id.cnab_state = "exported"
        return result
