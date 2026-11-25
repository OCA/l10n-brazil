# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Link the IS account tax group to the fiscal IS tax group.

`l10n_br_coa` creates the `tax_group_is` account tax group in the companies
that already had the chart (its own migration, which runs before the fiscal
fields exist). The account taxes only follow the fiscal taxes through
`fiscal_tax_group_id`, so the link is made here, when the field is available.
"""

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


def link_is_groups(env):
    fiscal_group = env.ref("l10n_br_fiscal.tax_group_is", raise_if_not_found=False)
    if not fiscal_group:
        return
    names = [
        f"{company.id}_tax_group_is"
        for company in env["res.company"].with_context(active_test=False).search([])
    ]
    imd_domain = [
        ("model", "=", "account.tax.group"),
        ("module", "in", ("account", "l10n_br_coa")),
        ("name", "in", names),
    ]
    groups = env["account.tax.group"]
    for imd in env["ir.model.data"].sudo().search(imd_domain):
        groups |= env["account.tax.group"].browse(imd.res_id).exists()
    groups = groups.filtered(lambda group: not group.fiscal_tax_group_id)
    groups.write({"fiscal_tax_group_id": fiscal_group.id})
    _logger.info("l10n_br_account: %s IS tax group(s) linked", len(groups))


@openupgrade.migrate()
def migrate(env, version):
    link_is_groups(env)
