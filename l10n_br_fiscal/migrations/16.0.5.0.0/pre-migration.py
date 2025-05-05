# Copyright (C) 2025 - TODAY - Raphaël Valyi - Akretion <raphael.valyi@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openupgradelib import openupgrade
from psycopg2.extras import execute_values

to_install = "uom_alias"


def install_new_modules(cr):
    sql = f"""
    UPDATE ir_module_module
    SET state='to install'
    WHERE name = '{to_install}' AND state='uninstalled'
    """
    openupgrade.logged_query(cr, sql)


@openupgrade.migrate()
def migrate(env, version):
    install_new_modules(env.cr)
    openupgrade.logged_query(env.cr, "DELETE from ir_model WHERE model = 'uom.alias'")
    openupgrade.logged_query(
        env.cr,
        "SELECT id, uom_id, code, write_uid, create_uid, "
        "write_date, create_date FROM uom_uom_alternative",
    )
    alternatives = env.cr.fetchall()
    openupgrade.rename_models(
        env.cr,
        [
            (
                "uom.uom.alternative",
                "uom.alias",
            ),
        ],
    )
    execute_values(
        env.cr,
        """INSERT INTO uom_alias
        (id, uom_id, code, write_uid, create_uid, write_date, create_date)
        VALUES %s""",
        alternatives,
        template="(%s, %s, %s, %s, %s, %s, %s)",  # Ensures proper escaping
    )

    # avoid deleting uom.alias model, table and columns
    # along with the old ir.model.data records:
    openupgrade.logged_query(
        env.cr,
        "DELETE FROM ir_model_data WHERE name = 'model_uom_alias' "
        "and module = 'l10n_br_fiscal'",
    )
    openupgrade.logged_query(
        env.cr,
        "DELETE FROM ir_model_data where model='ir.model.fields' "
        "and module = 'l10n_br_fiscal' and name ilike 'field_uom_uom__%'",
    )
    openupgrade.logged_query(
        env.cr,
        "DELETE FROM ir_model_data where model='ir.model.fields' "
        "and module = 'l10n_br_fiscal' and name ilike 'field_uom_alias__%'",
    )
