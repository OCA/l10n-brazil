# Copyright 2023 Engenere - Antônio S. P. Neto
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET fiscal_document_id = ai.fiscal_document_id
        FROM account_invoice ai
        WHERE ai.id = am.old_invoice_id AND ai.fiscal_document_id IS NOT NULL
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move_line aml
        SET fiscal_document_line_id = COALESCE(
            ail.fiscal_document_line_id, aml.fiscal_document_line_id),
            wh_move_line_id = COALESCE(ail.wh_move_line_id, aml.wh_move_line_id)
        FROM account_invoice_line ail
        WHERE aml.old_invoice_line_id = ail.id AND
            (ail.fiscal_document_line_id IS NOT NULL
            OR ail.wh_move_line_id IS NOT NULL)
        """,
    )
