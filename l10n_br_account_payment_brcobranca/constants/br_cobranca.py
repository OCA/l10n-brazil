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
