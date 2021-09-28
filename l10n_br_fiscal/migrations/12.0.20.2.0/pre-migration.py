# Copyright (C) 2021 - Renato Lima - Akretion
# License AGPL-3.0 or later (
# http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE
            l10n_br_fiscal_document
        SET
            document_key = regexp_replace(document_key, '[^0-9]+', '', 'g')
        """,
    )

    openupgrade.logged_query(
        env.cr,
        """
        UPDATE
            l10n_br_fiscal_document_related
        SET
            document_key = regexp_replace(document_key, '[^0-9]+', '', 'g')
        """,
    )
