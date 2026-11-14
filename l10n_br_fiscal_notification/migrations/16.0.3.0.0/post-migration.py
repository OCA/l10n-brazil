# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.column_exists(
        env.cr, "l10n_br_fiscal_document_email", "state_edoc"
    ):
        return

    openupgrade.logged_query(
        env.cr,
        """
        UPDATE l10n_br_fiscal_document_email
        SET state_autorizada = state_edoc IS NULL OR state_edoc = 'autorizada',
            state_cancelada = state_edoc IS NULL OR state_edoc = 'cancelada',
            state_denegada = state_edoc IS NULL OR state_edoc = 'denegada'
        """,
    )

    definitions = (
        env["l10n_br_fiscal.document.email"].with_context(active_test=False).search([])
    )
    definitions.invalidate_recordset()
    definitions._compute_name()
