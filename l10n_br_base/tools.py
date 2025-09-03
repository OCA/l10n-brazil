# Copyright (C) 2009-Today - Akretion (<http://www.akretion.com>).
# @author Gabriel C. Stabel - Akretion
# @author Renato Lima <renato.lima@akretion.com.br>
# @author Raphael Valyi <raphael.valyi@akretion.com>
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from erpbrasil.base.fiscal import cnpj_cpf, ie

from odoo.exceptions import ValidationError


def check_ie(env, l10n_br_ie_code, state, country):
    """
    Checks if 'Inscrição Estadual' field is valid
    using erpbrasil library
    :param env:
    :param l10n_br_ie_code:
    :param state:
    :param country:
    :return:
    """
    if env and l10n_br_ie_code and state and country:
        if country != env.ref("base.br"):
            return  # skip check

        disable_ie_validation = env["ir.config_parameter"].sudo().get_param(
            "l10n_br_base.disable_ie_validation", default=False
        ) or env.context.get("disable_ie_validation")

        if disable_ie_validation:
            return  # skip check

        # TODO: em aberto debate sobre:
        #  Se no caso da empresa ser 'isenta' do IE o campo
        #  deve estar vazio ou pode ter algum valor como abaixo
        if l10n_br_ie_code in ("isento", "isenta", "ISENTO", "ISENTA"):
            return  # skip check

        if not ie.validar(state.code.lower(), l10n_br_ie_code):
            raise ValidationError(
                env._(
                    "Estadual Inscription %(inscr)s Invalid for State %(state)s!",
                    inscr=l10n_br_ie_code,
                    state=state.name,
                )
            )


def check_cnpj_cpf(env, cnpj_cpf_value, country, force_validation=False):
    """
    Check CNPJ or CPF is valid using erpbrasil library
    :param env:
    :param cnpj_cpf_value:
    :param country:
    :return:
    """
    if env and cnpj_cpf_value and country:
        if country == env.ref("base.br"):
            disable_cpf_cnpj_validation = env["ir.config_parameter"].sudo().get_param(
                "l10n_br_base.disable_cpf_cnpj_validation", default=False
            ) or env.context.get("disable_cpf_cnpj_validation")

            if not disable_cpf_cnpj_validation or force_validation:
                # Removendo . / - para diferenciar o CNPJ do CPF
                # 62.228.384/0001-51 -CNPJ
                # 62228384000151 - CNPJ
                # 765.865.078-12 - CPF
                # 76586507812 - CPF
                clean_cnpj_cpf_value = "".join(
                    char for char in cnpj_cpf_value if char.isdigit()
                )
                error_msg = False
                if len(clean_cnpj_cpf_value) not in (11, 14):
                    error_msg = env._(
                        "The size of CPF must have 11 and the CNPJ 14 digits "
                        "without dot, dash and slash; in this case:\n\n"
                        "CPF or CNPJ: %(d_clean_id)s\n"
                        "Size: %(d_size_id)s",
                        d_clean_id=clean_cnpj_cpf_value,
                        d_size_id=len(clean_cnpj_cpf_value),
                    )
                elif not cnpj_cpf.validar(cnpj_cpf_value):
                    document = "CPF"
                    if len(clean_cnpj_cpf_value) == 14:
                        document = "CNPJ"
                    error_msg = env._(
                        "%(d_type)s %(d_id)s is invalid!",
                        d_type=document,
                        d_id=cnpj_cpf_value,
                    )

                if error_msg:
                    raise ValidationError(error_msg)
