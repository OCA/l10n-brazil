# Copyright 2017 Akretion
# @author Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from ..constants.br_cobranca import DICT_BRCOBRANCA_CURRENCY, get_brcobranca_bank

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Campo tecnico para ser usado na busca da account.move.line de
    # reconciliação, no caso da Linha de Liquidação é preenchido com
    # Nosso Número e nos outros casos é o campo Número do Documento
    # TODO: Teria alguma forma de fazer sem esse campo? Ou outro campo
    #  a ser usado sem a necessidade de criar um novo
    cnab_returned_ref = fields.Char(string="CNAB Returned Reference", copy=False)

    # see the list of brcobranca boleto fields:
    # https://github.com/kivanio/brcobranca/blob/master/lib/
    # brcobranca/boleto/base.rb
    # and test a here:
    # https://github.com/kivanio/brcobranca/blob/master/spec/
    # brcobranca/boleto/itau_spec.rb

    def send_payment(self):

        # super(AccountMoveLine, self).send_payment()
        wrapped_boleto_list = []

        for move_line in self:

            bank_account_id = move_line.payment_mode_id.fixed_journal_id.bank_account_id
            bank_name_brcobranca = get_brcobranca_bank(
                bank_account_id, move_line.payment_mode_id.payment_method_code
            )
            precision = self.env["decimal.precision"]
            precision_account = precision.precision_get("Account")

            boleto_cnab_api_data = {
                "bank": bank_name_brcobranca[0],
                "valor": str("%.2f" % move_line.debit),
                "cedente": move_line.company_id.partner_id.legal_name,
                "cedente_endereco": (move_line.company_id.partner_id.street_name or "")
                + ", "
                + (move_line.company_id.partner_id.street_number or "")
                + " - "
                + (move_line.company_id.partner_id.district or "")
                + " - "
                + (move_line.company_id.partner_id.city_id.name or "")
                + " - "
                + ("CEP:" + move_line.company_id.partner_id.zip or "")
                + " - "
                + (move_line.company_id.partner_id.state_id.code or ""),
                "documento_cedente": move_line.company_id.cnpj_cpf,
                "sacado": move_line.partner_id.legal_name,
                "sacado_documento": move_line.partner_id.cnpj_cpf,
                "agencia": bank_account_id.bra_number,
                "conta_corrente": bank_account_id.acc_number,
                "convenio": move_line.payment_mode_id.code_convetion,
                "carteira": str(move_line.payment_mode_id.boleto_wallet),
                "nosso_numero": int(
                    "".join(i for i in move_line.own_number if i.isdigit())
                ),
                "documento_numero": move_line.document_number,
                "data_vencimento": move_line.date_maturity.strftime("%Y/%m/%d"),
                "data_documento": move_line.move_id.invoice_date.strftime("%Y/%m/%d"),
                "especie": move_line.payment_mode_id.boleto_species,
                "moeda": DICT_BRCOBRANCA_CURRENCY["R$"],
                "aceite": move_line.payment_mode_id.boleto_accept,
                "sacado_endereco": (move_line.partner_id.street_name or "")
                + ", "
                + (move_line.partner_id.street_number or "")
                + " "
                + (move_line.partner_id.city_id.name or "")
                + " - "
                + (move_line.partner_id.state_id.name or ""),
                "data_processamento": move_line.move_id.invoice_date.strftime(
                    "%Y/%m/%d"
                ),
                "instrucao1": move_line.payment_mode_id.instructions or "",
            }

            # Instrução de Juros
            if move_line.payment_mode_id.boleto_interest_perc > 0.0:
                valor_juros = round(
                    move_line.debit
                    * ((move_line.payment_mode_id.boleto_interest_perc / 100) / 30),
                    precision_account,
                )
                instrucao_juros = (
                    "APÓS VENCIMENTO COBRAR PERCENTUAL"
                    + " DE %s %% AO MÊS ( R$ %s AO DIA )"
                    % (
                        (
                            "%.2f" % move_line.payment_mode_id.boleto_interest_perc
                        ).replace(".", ","),
                        ("%.2f" % valor_juros).replace(".", ","),
                    )
                )
                boleto_cnab_api_data.update(
                    {
                        "instrucao3": instrucao_juros,
                    }
                )

            # Instrução Multa
            if move_line.payment_mode_id.boleto_fee_perc > 0.0:
                valor_multa = round(
                    move_line.debit * (move_line.payment_mode_id.boleto_fee_perc / 100),
                    precision_account,
                )
                instrucao_multa = (
                    "APÓS VENCIMENTO COBRAR MULTA"
                    + " DE %s %% ( R$ %s )"
                    % (
                        ("%.2f" % move_line.payment_mode_id.boleto_fee_perc).replace(
                            ".", ","
                        ),
                        ("%.2f" % valor_multa).replace(".", ","),
                    )
                )
                boleto_cnab_api_data.update(
                    {
                        "instrucao4": instrucao_multa,
                    }
                )

            # Instrução Desconto
            if move_line.payment_mode_id.boleto_discount_perc > 0.0:
                valor_desconto = round(
                    move_line.debit
                    * (move_line.payment_mode_id.boleto_discount_perc / 100),
                    precision_account,
                )
                instrucao_desconto_vencimento = (
                    "CONCEDER ABATIMENTO PERCENTUAL DE" + " %s %% "
                    "ATÉ O VENCIMENTO EM %s ( R$ %s )"
                    % (
                        (
                            "%.2f" % move_line.payment_mode_id.boleto_discount_perc
                        ).replace(".", ","),
                        move_line.date_maturity.strftime("%d/%m/%Y"),
                        ("%.2f" % valor_desconto).replace(".", ","),
                    )
                )
                boleto_cnab_api_data.update(
                    {
                        "instrucao5": instrucao_desconto_vencimento,
                    }
                )

            bank_account = move_line.payment_mode_id.fixed_journal_id.bank_account_id
            if bank_account_id.bank_id.code_bc in ("021", "004"):
                boleto_cnab_api_data.update(
                    {
                        "digito_conta_corrente": bank_account.acc_number_dig,
                    }
                )

            # Fields used in Sicredi and Sicoob Banks
            if bank_account_id.bank_id.code_bc in ("748", "756"):
                boleto_cnab_api_data.update(
                    {
                        "byte_idt": move_line.payment_mode_id.boleto_byte_idt,
                        "posto": move_line.payment_mode_id.boleto_post,
                    }
                )
            # Campo usado no Unicred
            if bank_account_id.bank_id.code_bc == "136":
                boleto_cnab_api_data.update(
                    {
                        "conta_corrente_dv": bank_account.acc_number_dig,
                    }
                )

            wrapped_boleto_list.append(boleto_cnab_api_data)

        return wrapped_boleto_list
