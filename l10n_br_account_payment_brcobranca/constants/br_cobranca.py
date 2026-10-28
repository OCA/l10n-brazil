# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# Copyright 2020 KMEE
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
from collections import namedtuple

from odoo import _
from odoo.exceptions import UserError
from odoo.tools import config

TIMEOUT = 300  # seconds

DICT_BRCOBRANCA_CNAB_TYPE = {
    "240": "cnab240",
    "400": "cnab400",
}

BankRecord = namedtuple("Bank", "name, retorno, remessa")

DICT_BRCOBRANCA_BANK = {
    "001": BankRecord("banco_brasil", retorno=["400"], remessa=["240", "400"]),
    "004": BankRecord("banco_nordeste", retorno=["400"], remessa=["400"]),
    "021": BankRecord("banestes", retorno=[], remessa=[]),
    "033": BankRecord("santander", retorno=["400", "240"], remessa=["400", "240"]),
    "041": BankRecord("banrisul", retorno=["400"], remessa=["400"]),
    "070": BankRecord("banco_brasilia", retorno=[], remessa=["400"]),
    "085": BankRecord("ailos", retorno=["240"], remessa=["240"]),
    "097": BankRecord("credisis", retorno=["400"], remessa=["400"]),
    "104": BankRecord("caixa", retorno=["240"], remessa=["240"]),
    "136": BankRecord("unicred", retorno=["400"], remessa=["240", "400"]),
    "237": BankRecord("bradesco", retorno=["400"], remessa=["400"]),
    "341": BankRecord("itau", retorno=["400"], remessa=["400"]),
    "399": BankRecord("hsbc", retorno=[], remessa=[]),
    "745": BankRecord("citibank", retorno=[], remessa=["400"]),
    "748": BankRecord("sicredi", retorno=["240"], remessa=["240"]),
    "756": BankRecord("sicoob", retorno=["240"], remessa=["240", "400"]),
}

DICT_BRCOBRANCA_CURRENCY = {
    "R$": "9",
}

# Dados do Split Payment do IBS/CBS (LC 214/2025) que o BRCobranca informa em
# cada linha de título do retorno quando o arquivo tem os registros opcionais
# Segmento X-03 (dados fiscais e valores de CBS/IBS) e X-04 (valores da
# liquidação do boleto) do Retorno de Cobrança do Layout Padrão Febraban 240
# posições V11.0, veja https://github.com/OCA/l10n-brazil/issues/5146 .
# Chave no JSON do BRCobranca (nome do atributo da gem na linha do retorno) ->
# campo do l10n_br_cnab.return.event: os campos de texto vão como vieram e os
# de valor passam por CNABFileParser.cnab_str_to_float.
DICT_SPLIT_PAYMENT_CHAR_FIELDS = {
    "documento_fiscal": "split_payment_document_key",
    "id_split": "split_payment_identifier",
    "tipo_id_split": "split_payment_identifier_type",
}
DICT_SPLIT_PAYMENT_VALUE_FIELDS = {
    "valor_cbs_informado": "split_payment_cbs_informed",
    "valor_ibs_informado": "split_payment_ibs_informed",
    "valor_cbs_corrigido": "split_payment_cbs_corrected",
    "valor_ibs_corrigido": "split_payment_ibs_corrected",
    "valor_cbs_em_aberto": "split_payment_cbs_open",
    "valor_ibs_em_aberto": "split_payment_ibs_open",
    "valor_cbs_segregado": "split_payment_cbs_segregated",
    "valor_ibs_segregado": "split_payment_ibs_segregated",
    "valor_pago_ausente_split": "split_payment_absent_value",
    "valor_repassado_novo_titular": "split_payment_transferred_value",
    "valor_residual": "split_payment_residual_value",
}


def get_brcobranca_bank(bank_account_id, payment_method_code):
    bank_name_brcobranca = DICT_BRCOBRANCA_BANK.get(bank_account_id.bank_id.code_bc)

    # Metodo get_brcobranca_bank chamado apenas nos casos de Remessa,
    # por isso apenas esse caso é validado.
    cnab_remessa = bank_name_brcobranca[2]
    if not bank_name_brcobranca or payment_method_code not in cnab_remessa:
        # Lista de bancos não implentados no BRCobranca
        raise UserError(
            _(
                "The Bank %(bank)s CNAB %(cnab_code)s is not implemented "
                "in BRCobranca.",
                bank=bank_account_id.bank_id.name,
                cnab_code=payment_method_code,
            )
        )
    return bank_name_brcobranca


def get_brcobranca_api_url(env):
    brcobranca_api_url = (
        os.environ.get("BRCOBRANCA_API_URL")
        or config.get("brcobranca_api_url")
        or env["ir.config_parameter"].sudo().get_param("brcobranca_api_url")
    )

    if not brcobranca_api_url:
        raise UserError(
            _(
                "BRCobranca API URL is not configured.\n\n"
                " Set the URL using one of the these methods:\n\n"
                "1. Set the environment variable:"
                " BRCOBRANCA_API_URL=http://boleto_cnab_api:9292\n"
                "2. Configure the URL in Odoo configuration file:"
                " brcobranca_api_url=http://boleto_cnab_api:9292\n"
                "3. Set the URL in System Parameters:"
                " brcobranca_api_url=http://boleto_cnab_api:9292\n"
            )
        )

    return brcobranca_api_url


# Caso Santander 400 precisa enviar o Nosso Numero com DV isso não acontece no
# 240, por enquanto é o único caso mapeado.
# Houve um PR https://github.com/kivanio/brcobranca/pull/236 na lib buscando
# resolver isso e foi apontando a contradição em ter para esse mesmo banco no
# caso do 400 a necessidade de informar o DV mas não precisar no 240,
# mas o mantedor da biblioteca não aceito a alteração.
# A melhor solução talvez seja ver a possibilidade de incluir ou fazer algo
# semelhante ao git-aggregator https://github.com/acsone/git-aggregator
# na API e com isso incluir um commit de outro repositorio que faça essa
# simples alteração porém mantendo a API ligada diretamente ao repo pricipal
# do BRcobranca, já que não existe o interesse em manter um Fork e um simples
# commit resolve o problema, por enquanto o calculo esta sendo feito aqui, se
# necessário ou isso for útil para outros casos pode ser visto de migrar esse
# calculo do modulo11 para um lugar genereico e facilitar seu uso exemplo
# l10n_br_account_payment_order/tools.py
def modulo11(num, base=9, r=0):
    soma = 0
    fator = 2
    for c in reversed(num):
        soma += int(c) * fator
        if fator == base:
            fator = 1
        fator += 1
    if r == 0:
        soma = soma * 10
        digito = soma % 11
        if digito == 10:
            digito = 0
        return digito
    if r == 1:
        resto = soma % 11
        return resto
