# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

_LEGACY_TABLE = "l10n_br_fiscal_certificate"
_TMP_TABLE = "l10n_br_fiscal_certificate_migration"


def _company_by_legacy_cert_id(env):
    env.cr.execute(
        "SELECT id, certificate_nfe_id, certificate_ecnpj_id FROM res_company"
    )
    mapping = {}
    for company_id, nfe_id, ecnpj_id in env.cr.fetchall():
        if nfe_id:
            mapping.setdefault(nfe_id, company_id)
        if ecnpj_id:
            mapping.setdefault(ecnpj_id, company_id)
    return mapping


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not openupgrade.table_exists(env.cr, _TMP_TABLE):
        return

    company_by_old = _company_by_legacy_cert_id(env)
    main_company = env.ref("base.main_company", raise_if_not_found=False)
    fallback_company_id = main_company.id if main_company else None

    certificate_model = env["certificate.certificate"]
    old_new = {}

    env.cr.execute(
        f"SELECT legacy_id, file, password, type, subtype, active "
        f"FROM {_TMP_TABLE} ORDER BY legacy_id"
    )
    for old_id, file, password, ctype, subtype, active in env.cr.fetchall():
        vals = {
            "content": file,
            "pkcs12_password": password,
            "type": ctype,
            "subtype": subtype,
            "active": active,
            "scope": "l10n_br",
            "company_id": company_by_old.get(old_id, fallback_company_id),
        }
        try:
            # Core re-parses ``content`` and derives pem_certificate, dates,
            # subject_common_name, serial_number and the private key. Its
            # ``_constrains_certificate_loaded`` rejects unparseable files, which
            # the legacy module also rejected on create, so this is a no-op in
            # practice.
            old_new[old_id] = certificate_model.create(vals).id
        except Exception:  # noqa: BLE001
            _logger.exception(
                "Skipping legacy certificate %s: could not be re-parsed", old_id
            )

    # Repoint the res.company foreign keys to the new certificate IDs.
    for old_id, new_id in old_new.items():
        env.cr.execute(
            "UPDATE res_company SET certificate_nfe_id = %s "
            "WHERE certificate_nfe_id = %s",
            (new_id, old_id),
        )
        env.cr.execute(
            "UPDATE res_company SET certificate_ecnpj_id = %s "
            "WHERE certificate_ecnpj_id = %s",
            (new_id, old_id),
        )

    # Cleanup.
    env.cr.execute(f"DROP TABLE IF EXISTS {_TMP_TABLE}")
    if openupgrade.table_exists(env.cr, _LEGACY_TABLE):
        env.cr.execute(f"DROP TABLE IF EXISTS {_LEGACY_TABLE}")
