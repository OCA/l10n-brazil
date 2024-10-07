# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

_column_renames = {
    "res_company": [
        ("sale_create_invoice_policy", "sale_invoicing_policy"),
    ],
}


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "res_company", "sale_create_invoice_policy"):
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE res_company
            SET sale_invoicing_policy = sale_create_invoice_policy;
            """,
        )

        # Apagando campos para evitar mensagem 'HINT ...'
        # Deleting field res.company.sale_create_invoice_policy
        # (hint: fields should be explicitly removed by an upgrade script)
        openupgrade.logged_query(
            env.cr,
            """
            DELETE FROM ir_model_fields WHERE name = 'sale_create_invoice_policy'
            """,
        )
        openupgrade.logged_query(
            env.cr,
            """
            DELETE FROM ir_model_fields WHERE name = 'button_create_invoice_invisible'
            """,
        )
