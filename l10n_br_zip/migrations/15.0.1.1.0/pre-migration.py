# Copyright 2024 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    sql = """UPDATE ir_config_parameter SET value = 'viacep'
    WHERE key = 'l10n_zip.cep_ws_provider' and value = 'correios';"""
    openupgrade.logged_query(env.cr, sql)
