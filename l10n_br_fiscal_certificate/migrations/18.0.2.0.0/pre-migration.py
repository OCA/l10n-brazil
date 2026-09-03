# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openupgradelib import openupgrade

_TMP_TABLE = "l10n_br_fiscal_certificate_migration"


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    """Snapshot the legacy certificates before the model is replaced.

    The old ``l10n_br_fiscal.certificate`` model is merged into the Odoo core
    ``certificate.certificate`` model. We read it here (while the ORM still knows
    the old model) and stash the payload into a temporary table, because the
    ``file`` binary lives in ``ir.attachment`` and can no longer be read through
    the ORM once the model is gone.
    """
    try:
        legacy_model = env["l10n_br_fiscal.certificate"]
    except KeyError:
        return

    legacy_certs = legacy_model.sudo().search([])
    if not legacy_certs:
        return

    openupgrade.logged_query(
        env.cr,
        f"""
        CREATE TABLE IF NOT EXISTS {_TMP_TABLE} (
            legacy_id INTEGER PRIMARY KEY,
            file TEXT,
            password VARCHAR,
            type VARCHAR,
            subtype VARCHAR,
            active BOOLEAN
        )
        """,
    )
    for cert in legacy_certs:
        openupgrade.logged_query(
            env.cr,
            f"""
            INSERT INTO {_TMP_TABLE}
                (legacy_id, file, password, type, subtype, active)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                cert.id,
                cert.with_context(bin_size=False).file or None,
                cert.password,
                cert.type,
                cert.subtype,
                cert.active,
            ),
        )
