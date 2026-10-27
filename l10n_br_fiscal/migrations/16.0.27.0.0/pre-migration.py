# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Keep the totals of existing documents when icms_relief_type is added.

Before this version the ICMS relief was always deducted from the line total,
so documents issued by the company were transmitted with vNF deducted. Those
lines get indDeduzDeson = 1, the others get the new default 0.
"""

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(
        env.cr, "l10n_br_fiscal_document_line", "icms_relief_type"
    ):
        return
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE l10n_br_fiscal_document_line
        ADD COLUMN icms_relief_type VARCHAR DEFAULT '0'
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE l10n_br_fiscal_document_line
        ALTER COLUMN icms_relief_type DROP DEFAULT
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE l10n_br_fiscal_document_line line
        SET icms_relief_type = '1'
        FROM l10n_br_fiscal_document doc
        WHERE line.document_id = doc.id
            AND doc.issuer = 'company'
            AND COALESCE(line.icms_relief_value, 0) != 0
        """,
    )
