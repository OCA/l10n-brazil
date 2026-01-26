# Copyright (C) 2025  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

LEGACY_COMMON_MAPPING = {
    "em_digitacao": "draft",
    "cancelada": "cancel",
    "inutilizada": "cancel",
}

LEGACY_BASE_MAPPING = {
    "a_enviar": "open",
    "autorizada": "open",
    "enviada": "open",
    "rejeitada": "open",
    "denegada": "cancel",
}

LEGACY_EDI_MAPPING = {
    "a_enviar": "open",
    "enviada": "sending",
    "autorizada": "authorized",
    "rejeitada": "rejected",
    "denegada": "denied",
}


def _migrate_selection_values(cr, table, column, mapping, where_extra=None):
    """Map legacy selection values to their new values with SQL CASE."""
    if not openupgrade.table_exists(cr, table):
        return

    when_clauses = "\n".join(
        f"                WHEN '{old}' THEN '{new}'" for old, new in mapping.items()
    )
    old_values = ", ".join(f"'{value}'" for value in mapping)

    where_clause = f"{column} IN ({old_values})"
    if where_extra:
        where_clause = f"{where_clause} AND {where_extra}"

    sql_query = f"""
        UPDATE {table}
        SET {column} = CASE {column}
{when_clauses}
            ELSE {column}
        END
        WHERE {where_clause};
    """
    openupgrade.logged_query(cr, sql_query)


@openupgrade.migrate()
def migrate(env, version):
    edi_installed = openupgrade.is_module_installed(env.cr, "l10n_br_fiscal_edi")

    # 1) l10n_br_fiscal.document.state_edoc
    # Always migrate common legacy values.
    _migrate_selection_values(
        env.cr,
        "l10n_br_fiscal_document",
        "state_edoc",
        LEGACY_COMMON_MAPPING,
    )

    # Non-electronic documents always collapse to base fiscal states.
    _migrate_selection_values(
        env.cr,
        "l10n_br_fiscal_document",
        "state_edoc",
        LEGACY_BASE_MAPPING,
        where_extra="document_electronic = FALSE",
    )

    if edi_installed:
        # Electronic documents keep EDI semantics.
        _migrate_selection_values(
            env.cr,
            "l10n_br_fiscal_document",
            "state_edoc",
            LEGACY_EDI_MAPPING,
            where_extra="document_electronic = TRUE",
        )
    else:
        # Without fiscal_edi, all remaining legacy EDI values must collapse
        # to base fiscal states to avoid invalid values in base selection.
        _migrate_selection_values(
            env.cr,
            "l10n_br_fiscal_document",
            "state_edoc",
            LEGACY_BASE_MAPPING,
        )

    # 2) l10n_br_fiscal.document.email state (module depends on fiscal_edi)
    # Keep semantics for EDI-aware notification records.
    _migrate_selection_values(
        env.cr,
        "l10n_br_fiscal_document_email",
        "state_edoc",
        {**LEGACY_COMMON_MAPPING, **LEGACY_EDI_MAPPING},
    )

    # 3) l10n_br_fiscal.subsequent.operation generation_situation
    # Keep EDI semantics where applicable.
    _migrate_selection_values(
        env.cr,
        "l10n_br_fiscal_subsequent_operation",
        "generation_situation",
        {**LEGACY_COMMON_MAPPING, **LEGACY_EDI_MAPPING},
    )
