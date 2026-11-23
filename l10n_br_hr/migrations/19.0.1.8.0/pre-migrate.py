# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from erpbrasil.base import misc
from erpbrasil.base.fiscal import cnpj_cpf
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """Salvage the legacy hr_employee.cnpj_cpf ghost column and drop it.

    The column was introduced in 2022 but never displayed in any view nor
    read by any business logic. Any residual value is copied to the
    employee work contact (res.partner) vat, stored unformatted following
    the l10n_br_base convention, only when the partner has no vat yet, the
    value is a valid CNPJ/CPF and it is not already used by another
    partner (mirroring the res.partner _check_vat constraint that raw SQL
    bypasses). cnpj_cpf_stripped is synced as it is a stored computed
    field.
    """
    if not openupgrade.column_exists(env.cr, "hr_employee", "cnpj_cpf"):
        return
    env.cr.execute(
        """
        SELECT e.id, e.work_contact_id, e.cnpj_cpf, p.vat
          FROM hr_employee e
          JOIN res_partner p ON p.id = e.work_contact_id
         WHERE e.cnpj_cpf IS NOT NULL
           AND e.cnpj_cpf != ''
        """
    )
    salvaged = skipped = 0
    for employee_id, partner_id, legacy_value, partner_vat in env.cr.fetchall():
        if partner_vat:
            skipped += 1
            continue
        clean_value = misc.punctuation_rm(legacy_value)
        if not cnpj_cpf.validar(clean_value):
            skipped += 1
            _logger.info(
                "l10n_br_hr: legacy hr_employee(%s).cnpj_cpf %r is not a valid "
                "CNPJ/CPF, not salvaged to res_partner(%s).vat",
                employee_id,
                legacy_value,
                partner_id,
            )
            continue
        env.cr.execute(
            "SELECT 1 FROM res_partner WHERE vat = %s AND id != %s LIMIT 1",
            (clean_value, partner_id),
        )
        if env.cr.fetchone():
            skipped += 1
            _logger.info(
                "l10n_br_hr: legacy hr_employee(%s).cnpj_cpf %r already used by "
                "another partner, not salvaged to res_partner(%s).vat",
                employee_id,
                legacy_value,
                partner_id,
            )
            continue
        env.cr.execute(
            """
            UPDATE res_partner
               SET vat = %(vat)s,
                   cnpj_cpf_stripped = %(vat)s,
                   write_uid = %(uid)s,
                   write_date = NOW() AT TIME ZONE 'UTC'
             WHERE id = %(id)s
            """,
            {"vat": clean_value, "uid": env.uid, "id": partner_id},
        )
        salvaged += 1
    _logger.info(
        "l10n_br_hr: salvaged %s legacy hr_employee.cnpj_cpf values into "
        "res_partner.vat (%s skipped)",
        salvaged,
        skipped,
    )
    openupgrade.drop_columns(env.cr, [("hr_employee", "cnpj_cpf")])
