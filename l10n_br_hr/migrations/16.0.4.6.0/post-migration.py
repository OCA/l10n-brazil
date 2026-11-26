# Copyright (C) 2026 - TODAY KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from psycopg2 import sql

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

# xmlid of the obsolete CBO record: xmlid of its successor in the
# official MTE table of 2026-07-10 (same title, or the old title is now a
# synonym of the successor). Obsolete codes without a confirmed successor
# are only archived.
CBO_SUCCESSORS = {
    "287": "2551",  # 214355 -> 202110
    "678": "2542",  # 253105 -> 142325
    "840": "2633",  # 314605 -> 314845
    "912": "2637",  # 322105 -> 322705
    "910": "2638",  # 322115 -> 322710
    "911": "2639",  # 322120 -> 322715
    "908": "2640",  # 322125 -> 322720
    "1049": "2609",  # 354110 -> 253140
    "1231": "2696",  # 422215 -> 422335
    "1362": "2725",  # 517335 -> 517235
    "1359": "2724",  # 517315 -> 517230
    "1738": "1744",  # 722225 -> 722220
}


def _column_exists(cr, table, column):
    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    return bool(cr.fetchone())


def _many2one_columns(env):
    """Stored many2one columns pointing to l10n_br_hr.cbo, including the
    ones of modules that are not loaded yet in the registry."""
    env.cr.execute(
        """
        SELECT model, name FROM ir_model_fields
        WHERE relation = 'l10n_br_hr.cbo' AND ttype = 'many2one' AND store
        """
    )
    columns = []
    for model, field in env.cr.fetchall():
        if model in env.registry:
            table = env[model]._table
        else:
            table = model.replace(".", "_")
        if _column_exists(env.cr, table, field):
            columns.append((table, field))
    return columns


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    mapping = {}
    for old_xmlid, new_xmlid in CBO_SUCCESSORS.items():
        old = env.ref(f"l10n_br_hr.{old_xmlid}", raise_if_not_found=False)
        new = env.ref(f"l10n_br_hr.{new_xmlid}", raise_if_not_found=False)
        if old and new:
            mapping[old.id] = new.id
    for table, column in _many2one_columns(env):
        moved = 0
        for old_id, new_id in mapping.items():
            env.cr.execute(
                sql.SQL("UPDATE {table} SET {column} = %s WHERE {column} = %s").format(
                    table=sql.Identifier(table), column=sql.Identifier(column)
                ),
                (new_id, old_id),
            )
            moved += env.cr.rowcount
        _logger.info(
            "%s.%s: %s record(s) moved from obsolete CBO codes to their successors",
            table,
            column,
            moved,
        )
