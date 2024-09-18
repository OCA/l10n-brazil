# Copyright 2017 Akretion
# @author Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.l10n_br_account_payment_order.constants import (
    get_boleto_especie_short_name,
)

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
        # Desnecessario chamar o super aqui o metodo
        # que esta chamando já verifica isso.

        wrapped_boleto_list = []

        for move_line in self:
            bank_account_id = move_line.payment_mode_id.fixed_journal_id.bank_account_id
            bank_name_brcobranca = get_brcobranca_bank(
                bank_account_id, move_line.payment_mode_id.payment_method_code
            )
            cnab_config = move_line.payment_mode_id.cnab_config_id

            boleto_cnab_api_data = {
                "bank": bank_name_brcobranca[0],
                "valor": str("%.2f" % move_line.debit),
                "cedente": move_line.company_id.partner_id.legal_name,
                "cedente_endereco": (move_line.company_id.partner_id.street_name or "")
                + " "
                + (move_line.company_id.partner_id.street_number or "")
                + ", "
                + (move_line.company_id.partner_id.district or "")
                + ", "
                + (move_line.company_id.partner_id.city_id.name or "")
                + " - "
                + (move_line.company_id.partner_id.state_id.code or "")
                + " "
                + ("CEP:" + move_line.company_id.partner_id.zip or ""),
                "documento_cedente": move_line.company_id.cnpj_cpf,
                "sacado": move_line.partner_id.legal_name,
                "sacado_documento": move_line.partner_id.cnpj_cpf,
                "agencia": bank_account_id.bra_number,
                "conta_corrente": bank_account_id.acc_number,
                "convenio": cnab_config.cnab_company_bank_code,
                "carteira": str(cnab_config.boleto_wallet),
                "nosso_numero": int(
                    "".join(i for i in move_line.own_number if i.isdigit())
                ),
                "documento_numero": move_line.document_number,
                "data_vencimento": move_line.date_maturity.strftime("%Y/%m/%d"),
                "data_documento": move_line.move_id.invoice_date.strftime("%Y/%m/%d"),
                "especie": move_line.currency_id.symbol,
                "especie_documento": get_boleto_especie_short_name(
                    cnab_config.boleto_species
                ),
                "moeda": DICT_BRCOBRANCA_CURRENCY["R$"],
                "aceite": cnab_config.boleto_accept,
                "sacado_endereco": (move_line.partner_id.street_name or "")
                + " "
                + (move_line.partner_id.street_number or "")
                + ", "
                + (move_line.partner_id.district or "")
                + ", "
                + (move_line.partner_id.city_id.name or "")
                + " - "
                + (move_line.partner_id.state_id.code or "")
                + " "
                + ("CEP:" + move_line.partner_id.zip or ""),
                "data_processamento": move_line.move_id.invoice_date.strftime(
                    "%Y/%m/%d"
                ),
                "instrucao1": cnab_config.instructions or "",
            }

            # Instrução de Juros
            if cnab_config.boleto_interest_perc > 0.0:
                valor_juros = move_line.currency_id.round(
                    move_line.debit * ((cnab_config.boleto_interest_perc / 100) / 30),
                )
                percentual_formatado = (
                    f"{cnab_config.boleto_interest_perc:.2f}".replace(".", ",")
                )
                juros_formatado = f"{valor_juros:.2f}".replace(".", ",")
                instrucao_juros = (
                    f"APÓS VENCIMENTO COBRAR PERCENTUAL DE {percentual_formatado}%"
                    f" AO MÊS (R${juros_formatado} AO DIA)"
                )
                boleto_cnab_api_data.update(
                    {
                        "instrucao3": instrucao_juros,
                    }
                )

            # Instrução Multa
            if cnab_config.boleto_fee_perc > 0.0:
                valor_multa = move_line.currency_id.round(
                    move_line.debit * (cnab_config.boleto_fee_perc / 100),
                )
                percentual_formatado = f"{cnab_config.boleto_fee_perc:.2f}".replace(
                    ".", ","
                )
                multa_formatado = f"{valor_multa:.2f}".replace(".", ",")
                instrucao_multa = (
                    f"APÓS VENCIMENTO COBRAR MULTA DE {percentual_formatado}%"
                    f" (R${multa_formatado})"
                )
                boleto_cnab_api_data.update(
                    {
                        "instrucao4": instrucao_multa,
                    }
                )

            # Instrução Desconto
            if move_line.boleto_discount_perc > 0.0:
                valor_desconto = move_line.currency_id.round(
                    move_line.debit * (move_line.boleto_discount_perc / 100),
                )
                percentual_formatado = f"{move_line.boleto_discount_perc:.2f}".replace(
                    ".", ","
                )
                desconto_formatado = f"{valor_desconto:.2f}".replace(".", ",")
                vencimento_formatado = move_line.date_maturity.strftime("%d/%m/%Y")
                instrucao_desconto_vencimento = (
                    f"CONCEDER DESCONTO DE {percentual_formatado}% "
                    f"ATÉ O VENCIMENTO EM {vencimento_formatado} "
                    f"(R${desconto_formatado})"
                )
                boleto_cnab_api_data.update(
                    {
                        "instrucao5": instrucao_desconto_vencimento,
                    }
                )

            bank_account = move_line.payment_mode_id.fixed_journal_id.bank_account_id
            # Abaixo Campos Especificos de cada caso

            # 021 - BANCO DO ESTADO DO ESPIRITO SANTO
            # 004 - BANCO INTER
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
                        "byte_idt": cnab_config.boleto_byte_idt,
                        "posto": cnab_config.boleto_post,
                    }
                )
            # Campo usado no Unicred
            if bank_account_id.bank_id.code_bc == "136":
                boleto_cnab_api_data.update(
                    {
                        "conta_corrente_dv": bank_account.acc_number_dig,
                    }
                )

            # Campo Santander
            if bank_account_id.bank_id.code_bc == "033":
                # Caso Santander possui:
                # Codigo de Transmissao tamanho 20 no 400 no 240 e 15
                # Codigo do Convenio tamanho 7
                # no boleto é usado o convenio
                boleto_cnab_api_data.update(
                    {
                        "convenio": cnab_config.convention_code,
                    }
                )

            wrapped_boleto_list.append(boleto_cnab_api_data)

        return wrapped_boleto_list
