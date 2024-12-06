# Copyright 2024 - TODAY, Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(
        env.cr, "l10n_br_fiscal_document_supplement", "qrcode"
    ) and openupgrade.column_exists(
        env.cr, "l10n_br_fiscal_document_supplement", "nfe40_qrCode"
    ):
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE l10n_br_fiscal_document_supplement
            SET qrcode = "nfe40_qrCode"
            WHERE "nfe40_qrCode" IS NOT NULL;
            """,
        )
        openupgrade.drop_columns(
            env.cr, [("l10n_br_fiscal_document_supplement", "nfe40_qrCode")]
        )

    if openupgrade.column_exists(
        env.cr, "l10n_br_fiscal_document_supplement", "url_key"
    ) and openupgrade.column_exists(
        env.cr, "l10n_br_fiscal_document_supplement", "nfe40_urlChave"
    ):
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE l10n_br_fiscal_document_supplement
            SET url_key = "nfe40_urlChave"
            WHERE "nfe40_urlChave" IS NOT NULL;
            """,
        )
        openupgrade.drop_columns(
            env.cr, [("l10n_br_fiscal_document_supplement", "nfe40_urlChave")]
        )
