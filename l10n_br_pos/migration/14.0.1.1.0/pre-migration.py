# Copyright (C) 2023 - Ygor Carvalho - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_field_renames = [
    (
        "pos.config",
        "pos_config",
        "sat_ambiente",
        "sat_environment",
    ),
    (
        "pos.config",
        "pos_config",
        "cnpj_homologacao",
        "cnpj_homologation",
    ),
    (
        "pos.config",
        "pos_config",
        "ie_homologacao",
        "ie_homologation",
    ),
    (
        "pos.config",
        "pos_config",
        "numero_caixa",
        "cashier_number",
    ),
    (
        "pos.config",
        "pos_config",
        "cod_ativacao",
        "activation_code",
    ),
    (
        "pos.config",
        "pos_config",
        "assinatura_sat",
        "signature_sat",
    ),
    (
        "pos.config",
        "pos_config",
        "impressora",
        "printer",
    ),
    (
        "pos.config",
        "pos_config",
        "sessao_sat",
        "session_sat",
    ),
    (
        "res.company",
        "res_company",
        "ambiente_sat",
        "environment_sat",
    ),
]


def update_sat_environment_map(cr, env_map):
    if not env_map:
        return

    current_env, target_env = env_map.popitem()
    update_sat_environment(cr, current_env, target_env)
    update_sat_environment_map(cr, env_map)


def update_sat_environment(cr, current_env, target_env):
    sql = """
    UPDATE res_company
    SET ambiente_sat=%s
    WHERE ambiente_sat=%s
    """
    openupgrade.logged_query(cr, sql, (target_env, current_env))


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    env_map = {"homologacao": "homologation", "producao": "production"}
    openupgrade.rename_fields(env, _field_renames)
    update_sat_environment_map(env.cr, env_map)
