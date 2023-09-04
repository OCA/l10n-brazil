# Copyright 2023-TODAY Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unicodedata import normalize


def remove_non_ascii_characters(value):
    # TODO: Ver se existe a possibilidade de fazer essa conversão de
    #  caracteres de forma automatica em todos os campos na criação
    #  do XML, por enquanto isso esta sendo feito campo a campo em
    #  usando esse metodo.
    result = ""
    if value and type(value) == str:
        result = (
            normalize("NFKD", value)
            .encode("ASCII", "ignore")
            .decode("ASCII")
            .replace("\n", "")
            .replace("\r", "")
            .strip()
        )

    return result
