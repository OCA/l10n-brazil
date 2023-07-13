# Copyright (C) 2023  Felipe Zago - KMEE <felipe.zago@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from erpbrasil.base.fiscal.edoc import cnpj_cpf


def format_cnpj_cpf(val):
    return cnpj_cpf.formata(val)
