from openupgradelib import openupgrade


def migrate(cr, version):
    openupgrade.logged_query(
        cr,
        """
        ALTER TABLE account_move_line
        ALTER COLUMN fiscal_document_line_id DROP NOT NULL
        """,
    )
    openupgrade.logged_query(
        cr,
        """
        ALTER TABLE account_move
        ALTER COLUMN fiscal_document_id DROP NOT NULL
        """,
    )
    openupgrade.logged_query(
        cr,
        """
        UPDATE account_move_line
        SET fiscal_document_line_id = NULL
        WHERE move_id IN (
            SELECT am.id
            FROM account_move am
            INNER JOIN l10n_br_fiscal_document fd ON am.fiscal_document_id = fd.id
            WHERE fd.document_type_id IS NULL
        )
        OR exclude_from_invoice_tab = true
        """,
    )
    openupgrade.logged_query(
        cr,
        """
        UPDATE account_move am
        SET fiscal_document_id = NULL
        FROM l10n_br_fiscal_document fd
        WHERE am.fiscal_document_id = fd.id
        AND fd.document_type_id IS NULL
        """,
    )
