# Copyright (C) 2025  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


def _rename_fields(env):
    openupgrade.rename_fields(
        env,
        [
            (
                "l10n_br_fiscal.document",
                "l10n_br_fiscal_document",
                "state_edoc",
                "state",
            ),
        ],
    )

    sql_query = """
        UPDATE {table}
        SET {new_column} = CASE {new_column}
            WHEN 'em_digitacao' THEN 'draft'
            WHEN 'autorizado' THEN 'done'
            WHEN 'cancelado' THEN 'cancel'
            -- Importante: mantém o valor se não houver mapeamento
            -- os outros valores são tratados no script de migração
            -- do módulo l10n_br_fiscal_edi
            ELSE {new_column}
        END
        WHERE {new_column} IN (
            'em_digitacao', 'autorizado',
            'cancelado'
        );
    """.format(
        table="l10n_br_fiscal_document",
        new_column="state",
    )

    openupgrade.logged_query(env.cr, sql_query)


@openupgrade.migrate()
def migrate(env, version):
    _rename_fields(env)
