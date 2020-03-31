# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


def domain_field_codes(field_codes, field_name="code_unmasked",
                       delimiter=",", operator1="=",
                       operator2="=ilike", code_size=8):

    field_codes = field_codes.replace('.', '')
    list_codes = field_codes.split(delimiter)

    domain = []

    if (len(list_codes) > 1
            and operator1 not in ('!=', 'not ilike')
            and operator2 not in ('!=', 'not ilike')):
        domain += ['|'] * (len(list_codes) - 1)

    for n in list_codes:
        if len(n) == code_size:
            domain.append((field_name, operator1, n))

        if len(n) < code_size:
            domain.append((field_name, operator2, n + '%'))

    return domain
