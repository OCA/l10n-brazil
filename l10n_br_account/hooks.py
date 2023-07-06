# Copyright (C) 2019 - Raphaël Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api
from odoo.tools.sql import column_exists, create_column


def pre_init_hook(cr):
    """
    account.move and account.move.line inherits from
    l10n_br_account.fiscal_document and l10n_br_account.fiscal_document.line
    respectively.
    But the problem is that you may have existing invoice and lines (like demo
    data or because you were using Odoo before installing this module or because
    you use your Odoo instance for other countries than Brazil) so we should
    make the Odoo ORM happy for these records and we do that with dummy records
    that we use to fill these new foreign keys.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Create fiscal_document_id fields
    if not column_exists(cr, "account_move", "fiscal_document_id"):
        create_column(cr, "account_move", "fiscal_document_id", "INTEGER")

    # Create fiscal_document_line_id fields
    if not column_exists(cr, "account_move_line", "fiscal_document_line_id"):
        create_column(cr, "account_move_line", "fiscal_document_line_id", "INTEGER")

    companies = env["res.company"].search([])
    for company in companies:
        cr.execute(
            """
            UPDATE
                account_move
            SET fiscal_document_id=%s
            WHERE
                company_id=%s
            AND
                fiscal_document_id IS NULL;""",
            (company.fiscal_dummy_id.id, company.id),
        )
        cr.execute(
            """
            UPDATE
                account_move_line
            SET
                fiscal_document_line_id=%s
            WHERE
                company_id=%s
            AND
                fiscal_document_line_id IS NULL;""",
            (company.fiscal_dummy_id.fiscal_line_ids[0].id, company.id),
        )


def post_init_hook(cr, registry):
    """Relate fiscal taxes to account taxes."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    l10n_br_coa_charts = env["account.chart.template"].search(
        [("parent_id", "=", env.ref("l10n_br_coa.l10n_br_coa_template").id)]
    )

    for l10n_br_coa_chart in l10n_br_coa_charts:
        l10n_br_coa_chart.load_fiscal_taxes()
