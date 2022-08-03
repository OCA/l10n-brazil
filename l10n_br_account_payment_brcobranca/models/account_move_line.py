# Copyright 2017 Akretion
# @author Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging

import requests

from odoo import models
from odoo.exceptions import Warning as UserError

from ..constants.br_cobranca import (
    DICT_BRCOBRANCA_CURRENCY,
    get_brcobranca_api_url,
    get_brcobranca_bank,
)

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    # see the list of brcobranca boleto fields:
    # https://github.com/kivanio/brcobranca/blob/master/lib/
    # brcobranca/boleto/base.rb
    # and test a here:
    # https://github.com/kivanio/brcobranca/blob/master/spec/
    # brcobranca/boleto/itau_spec.rb

    def send_payment(self):
        wrapped_boleto_list = []
        for move_line in self:
            boleto_cnab_api_data = move_line._prepare_boleto_cnab_vals()
            wrapped_boleto_list.append(boleto_cnab_api_data)
        return wrapped_boleto_list

    def _prepare_boleto_cnab_vals(self):
        self.ensure_one()
        bank_account_id = self.payment_mode_id.fixed_journal_id.bank_account_id
        bank_name_brcobranca = get_brcobranca_bank(
            bank_account_id, self.payment_mode_id.payment_method_code
        )
        precision = self.env["decimal.precision"]
        precision_account = precision.precision_get("Account")

        boleto_cnab_api_data = {
            "bank": bank_name_brcobranca[0],
            "valor": str("%.2f" % self.debit),
            "cedente": self.company_id.partner_id.legal_name,
            "cedente_endereco": (self.company_id.partner_id.street_name or "")
            + ", "
            + (self.company_id.partner_id.street_number or "")
            + " - "
            + (self.company_id.partner_id.district or "")
            + " - "
            + (self.company_id.partner_id.city_id.name or "")
            + " - "
            + ("CEP:" + self.company_id.partner_id.zip or "")
            + " - "
            + (self.company_id.partner_id.state_id.code or ""),
            "documento_cedente": self.company_id.cnpj_cpf,
            "sacado": self.partner_id.legal_name,
            "sacado_documento": self.partner_id.cnpj_cpf,
            "agencia": bank_account_id.bra_number,
            "conta_corrente": bank_account_id.acc_number,
            "convenio": self.payment_mode_id.code_convetion,
            "carteira": str(self.payment_mode_id.boleto_wallet),
            "nosso_numero": int("".join(i for i in self.own_number if i.isdigit())),
            "documento_numero": self.document_number,
            "data_vencimento": self.date_maturity.strftime("%Y/%m/%d"),
            "data_documento": self.invoice_id.date_invoice.strftime("%Y/%m/%d"),
            "especie": self.payment_mode_id.boleto_species,
            "moeda": DICT_BRCOBRANCA_CURRENCY["R$"],
            "aceite": self.payment_mode_id.boleto_accept,
            "sacado_endereco": (self.partner_id.street_name or "")
            + ", "
            + (self.partner_id.street_number or "")
            + " "
            + (self.partner_id.city_id.name or "")
            + " - "
            + (self.partner_id.state_id.name or ""),
            "data_processamento": self.invoice_id.date_invoice.strftime("%Y/%m/%d"),
            "instrucao1": self.payment_mode_id.instructions or "",
        }

        # Instrução de Juros
        if self.payment_mode_id.boleto_interest_perc > 0.0:
            valor_juros = round(
                self.debit * ((self.payment_mode_id.boleto_interest_perc / 100) / 30),
                precision_account,
            )
            instrucao_juros = (
                "APÓS VENCIMENTO COBRAR PERCENTUAL"
                + " DE %s %% AO MÊS ( R$ %s AO DIA )"
                % (
                    ("%.2f" % self.payment_mode_id.boleto_interest_perc).replace(
                        ".", ","
                    ),
                    ("%.2f" % valor_juros).replace(".", ","),
                )
            )
            boleto_cnab_api_data.update(
                {
                    "instrucao3": instrucao_juros,
                }
            )

        # Instrução Multa
        if self.payment_mode_id.boleto_fee_perc > 0.0:
            valor_multa = round(
                self.debit * (self.payment_mode_id.boleto_fee_perc / 100),
                precision_account,
            )
            instrucao_multa = "APÓS VENCIMENTO COBRAR MULTA" + " DE %s %% ( R$ %s )" % (
                ("%.2f" % self.payment_mode_id.boleto_fee_perc).replace(".", ","),
                ("%.2f" % valor_multa).replace(".", ","),
            )
            boleto_cnab_api_data.update(
                {
                    "instrucao4": instrucao_multa,
                }
            )

        # Instrução Desconto
        if self.payment_mode_id.boleto_discount_perc > 0.0:
            valor_desconto = round(
                self.debit * (self.payment_mode_id.boleto_discount_perc / 100),
                precision_account,
            )
            instrucao_desconto_vencimento = (
                "CONCEDER ABATIMENTO PERCENTUAL DE" + " %s %% "
                "ATÉ O VENCIMENTO EM %s ( R$ %s )"
                % (
                    ("%.2f" % self.payment_mode_id.boleto_discount_perc).replace(
                        ".", ","
                    ),
                    self.date_maturity.strftime("%d/%m/%Y"),
                    ("%.2f" % valor_desconto).replace(".", ","),
                )
            )
            boleto_cnab_api_data.update(
                {
                    "instrucao5": instrucao_desconto_vencimento,
                }
            )

        if bank_account_id.bank_id.code_bc in ("021", "004"):
            boleto_cnab_api_data.update(
                {
                    "digito_conta_corrente": bank_account_id.acc_number_dig,
                }
            )

        # Fields used in Sicredi and Sicoob Banks
        if bank_account_id.bank_id.code_bc in ("748", "756"):
            boleto_cnab_api_data.update(
                {
                    "byte_idt": self.payment_mode_id.boleto_byte_idt,
                    "posto": self.payment_mode_id.boleto_post,
                }
            )
        # Campo usado no Unicred
        if bank_account_id.bank_id.code_bc == "136":
            boleto_cnab_api_data.update(
                {
                    "conta_corrente_dv": bank_account_id.acc_number_dig,
                }
            )
        # Particularidades Santander
        if bank_account_id.bank_id.code_bc in ("033"):
            boleto_cnab_api_data.update(
                {
                    # A carteira impressa no boleto é diferente da remessa.
                    "carteira": str(self.payment_mode_id.boleto_wallet2),
                }
            )
        return boleto_cnab_api_data

    def generate_own_number_boleto(self):
        """Consulta a API brcobranca e retorna o nosso número completo
        conforme o impresso no Boleto"""
        self.ensure_one()
        boleto_data = self._prepare_boleto_cnab_vals()
        bank = boleto_data.pop("bank")
        data = json.dumps(boleto_data, separators=(",", ":"))
        brcobranca_api_url = get_brcobranca_api_url(self.env)
        brcobranca_service_url = brcobranca_api_url + "/api/boleto/nosso_numero"
        res = requests.get(brcobranca_service_url, params={"bank": bank, "data": data})
        if str(res.status_code)[0] == "2":
            return res.text.strip('"')
        else:
            raise UserError(res.text.encode("utf-8"))
