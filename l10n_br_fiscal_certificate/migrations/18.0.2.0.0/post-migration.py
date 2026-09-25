# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

_LEGACY_MODEL = "l10n_br_fiscal.certificate"
_LEGACY_TABLE = "l10n_br_fiscal_certificate"
_TMP_TABLE = "l10n_br_fiscal_certificate_migration"
_TMP_COMPANY_TABLE = "l10n_br_fiscal_certificate_company_migration"


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not openupgrade.table_exists(env.cr, _TMP_TABLE):
        return

    env.cr.execute(
        f"SELECT company_id, field, legacy_id FROM {_TMP_COMPANY_TABLE} "
        "ORDER BY company_id, field"
    )
    company_links = env.cr.fetchall()
    company_ids_by_legacy = {}
    for company_id, _field, legacy_id in company_links:
        company_ids = company_ids_by_legacy.setdefault(legacy_id, [])
        if company_id not in company_ids:
            company_ids.append(company_id)

    # The legacy certificates were global while certificate.certificate
    # requires a company: a legacy certificate used by several companies
    # (e.g. a head office and its branches) is recreated in each of them.
    # The ones no company used go archived to the main company.
    main_company = env.ref("base.main_company", raise_if_not_found=False)
    fallback_company_ids = main_company.ids if main_company else []

    attachment_model = env["ir.attachment"]
    certificate_model = env["certificate.certificate"]
    new_ids = {}

    env.cr.execute(
        f"SELECT legacy_id, password, active FROM {_TMP_TABLE} ORDER BY legacy_id"
    )
    for legacy_id, password, active in env.cr.fetchall():
        attachment = attachment_model.search(
            [
                ("res_model", "=", _LEGACY_MODEL),
                ("res_field", "=", "file"),
                ("res_id", "=", legacy_id),
            ],
            limit=1,
        )
        if not attachment:
            _logger.warning("Skipping legacy certificate %s: no file", legacy_id)
            continue
        company_ids = company_ids_by_legacy.get(legacy_id)
        if not company_ids:
            company_ids, active = fallback_company_ids, False
        for company_id in company_ids:
            vals = {
                "content": attachment.datas,
                "pkcs12_password": password,
                "active": active,
                "scope": "l10n_br",
                "company_id": company_id,
            }
            try:
                # Core re-parses ``content`` and derives pem_certificate,
                # dates, subject_common_name, serial_number and the private
                # key; the savepoint discards a certificate it rejects.
                with env.cr.savepoint():
                    certificate = certificate_model.create(vals)
            except Exception:  # noqa: BLE001
                _logger.exception(
                    "Skipping legacy certificate %s for company %s: "
                    "could not be re-parsed",
                    legacy_id,
                    company_id,
                )
                continue
            new_ids[legacy_id, company_id] = certificate.id

    # The company keeps using the same certificate: the NF-e one, or the
    # e-CNPJ one when it had no NF-e certificate.
    certificate_by_company = {}
    for company_id, field, legacy_id in company_links:
        new_id = new_ids.get((legacy_id, company_id))
        if new_id and (
            company_id not in certificate_by_company or field == "certificate_nfe_id"
        ):
            certificate_by_company[company_id] = new_id
    for company_id, certificate_id in certificate_by_company.items():
        env.cr.execute(
            "UPDATE res_company SET certificate_id = %s WHERE id = %s",
            (certificate_id, company_id),
        )

    # Cleanup. CASCADE drops the foreign keys of the removed res.company
    # fields, whose columns are only dropped at the end of the upgrade.
    env.cr.execute(f"DROP TABLE IF EXISTS {_TMP_COMPANY_TABLE}")
    env.cr.execute(f"DROP TABLE IF EXISTS {_TMP_TABLE}")
    env.cr.execute(f"DROP TABLE IF EXISTS {_LEGACY_TABLE} CASCADE")
