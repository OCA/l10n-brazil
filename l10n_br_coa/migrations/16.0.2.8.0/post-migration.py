# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Carry the account classification from the chart templates to live accounts.

`account.account.template.tag_ids` only reaches `account.account` when the
chart is loaded into a company. On a database that already loaded the chart,
updating the module updates the template and not the account, and the reports
would read zero, because they select by classification.

The template to account mapping is the `ir.model.data` the chart load creates,
named `{company_id}_{template xmlid}`. That is the same path the core uses to
know which account came from which template, so it works for any chart, not
only the two shipped by the OCA.

The migration never removes an existing classification: whoever tagged an
account by hand keeps what they did.
"""
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    templates = env["account.account.template"].search([("tag_ids", "!=", False)])
    if not templates:
        return

    # {template id: tag ids}
    tags_by_template = {t.id: t.tag_ids.ids for t in templates}

    data = env["ir.model.data"].search(
        [
            ("model", "=", "account.account.template"),
            ("res_id", "in", list(tags_by_template)),
        ]
    )
    # {full template xmlid: tag ids}
    tags_by_xmlid = {f"{d.module}.{d.name}": tags_by_template[d.res_id] for d in data}
    if not tags_by_xmlid:
        return

    updated = 0
    for company in env["res.company"].search([]):
        suffix_map = {
            f"{company.id}_{name.split('.', 1)[1]}": tags
            for name, tags in tags_by_xmlid.items()
        }
        account_data = env["ir.model.data"].search(
            [
                ("model", "=", "account.account"),
                ("name", "in", list(suffix_map)),
            ]
        )
        for d in account_data:
            account = env["account.account"].browse(d.res_id).exists()
            if not account:
                continue
            missing = set(suffix_map[d.name]) - set(account.tag_ids.ids)
            if missing:
                account.write({"tag_ids": [(4, tag_id) for tag_id in missing]})
                updated += 1

    _logger.info("l10n_br_coa: classification applied to %s existing accounts", updated)
