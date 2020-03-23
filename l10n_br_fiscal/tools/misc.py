# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


def domain_field_codes(field_codes, field_name="code_unmasked",
                       delimiter=",", operator1="=",
                       operator2="=ilike", code_size=8):
    list_codes = field_codes.split(delimiter)

    domain = ['|'] * (len(list_codes) - 1)

    domain += [('code_unmasked', operator1, n)
               for n in list_codes if len(n) == code_size]

    domain += [('code_unmasked', operator2, n + '%')
               for n in list_codes if len(n) < code_size]

    return domain
