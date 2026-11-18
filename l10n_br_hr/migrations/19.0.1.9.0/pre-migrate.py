# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """Carry the employee nationality over to hr.version.

    l10n_br_hr used to declare its own country_id on hr.employee with a
    Brazilian default. Since 19.0 the country belongs to hr.version, and a
    local declaration silently shadows the inherited related field: the
    nationality stayed on an hr_employee column that no version and no
    payroll rule reads any more.
    """
    if not openupgrade.column_exists(env.cr, "hr_employee", "country_id"):
        return
    if not openupgrade.column_exists(env.cr, "hr_version", "country_id"):
        return
    env.cr.execute(
        """
        UPDATE hr_version v
           SET country_id = e.country_id
          FROM hr_employee e
         WHERE v.id = e.current_version_id
           AND v.country_id IS NULL
           AND e.country_id IS NOT NULL
        """
    )
    _logger.info(
        "l10n_br_hr: copied %s employee nationalities to hr.version",
        env.cr.rowcount,
    )
    openupgrade.drop_columns(env.cr, [("hr_employee", "country_id")])
