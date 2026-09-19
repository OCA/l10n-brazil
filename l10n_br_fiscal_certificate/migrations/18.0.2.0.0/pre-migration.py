# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openupgradelib import openupgrade

_LEGACY_TABLE = "l10n_br_fiscal_certificate"
_TMP_TABLE = "l10n_br_fiscal_certificate_migration"
_TMP_COMPANY_TABLE = "l10n_br_fiscal_certificate_company_migration"


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    """Snapshot the legacy certificates before the model is replaced.

    Pre-migration scripts run before the models of the module are loaded in
    the registry, so the legacy ``l10n_br_fiscal.certificate`` model can't be
    read through the ORM here: everything is done in SQL. The ``file`` binary
    lives in ``ir.attachment`` and is read in the post-migration.

    The ``res.company`` fields ``certificate_nfe_id`` and
    ``certificate_ecnpj_id`` are replaced by ``certificate_id``: their links
    are stashed to know in which companies each certificate must be recreated
    and which one each company uses.
    """
    cr = env.cr
    if not openupgrade.table_exists(cr, _LEGACY_TABLE):
        return

    openupgrade.logged_query(
        cr,
        f"""
        CREATE TABLE {_TMP_TABLE} AS
        SELECT id AS legacy_id, password, active
        FROM {_LEGACY_TABLE}
        """,
    )
    openupgrade.logged_query(
        cr,
        f"""
        CREATE TABLE {_TMP_COMPANY_TABLE} AS
        SELECT id AS company_id,
            'certificate_nfe_id' AS field,
            certificate_nfe_id AS legacy_id
        FROM res_company
        WHERE certificate_nfe_id IS NOT NULL
        UNION ALL
        SELECT id, 'certificate_ecnpj_id', certificate_ecnpj_id
        FROM res_company
        WHERE certificate_ecnpj_id IS NOT NULL
        """,
    )
