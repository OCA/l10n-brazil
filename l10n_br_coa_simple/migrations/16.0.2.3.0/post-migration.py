# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Correct financial-income classifications in existing simple charts.

Removing the expense tag is intentional because it was an error in the chart.
"""

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

SIMPLE_FINANCIAL_INCOME = (
    "account_template_3410201",
    "account_template_3410202",
    "account_template_3410203",
    "account_template_3410204",
)


@openupgrade.migrate()
def migrate(env, version):
    old_tag = env.ref(
        "l10n_br_coa.account_tag_expenses_financial", raise_if_not_found=False
    )
    new_tag = env.ref(
        "l10n_br_coa.account_tag_revenue_financial", raise_if_not_found=False
    )
    if not old_tag or not new_tag:
        return

    template_data = env["ir.model.data"].search(
        [
            ("model", "=", "account.account.template"),
            ("module", "=", "l10n_br_coa_simple"),
            ("name", "in", SIMPLE_FINANCIAL_INCOME),
        ]
    )
    if not template_data:
        return

    updated = 0
    for company in env["res.company"].search([]):
        account_names = [f"{company.id}_{template.name}" for template in template_data]
        account_data = env["ir.model.data"].search(
            [
                ("model", "=", "account.account"),
                ("module", "=", "l10n_br_coa_simple"),
                ("name", "in", account_names),
            ]
        )
        for data in account_data:
            account = env["account.account"].browse(data.res_id).exists()
            if not account:
                continue
            commands = []
            if old_tag in account.tag_ids:
                commands.append((3, old_tag.id))
            if new_tag not in account.tag_ids:
                commands.append((4, new_tag.id))
            if commands:
                account.write({"tag_ids": commands})
                updated += 1

    _logger.info("l10n_br_coa_simple: corrected %s financial-income accounts", updated)
