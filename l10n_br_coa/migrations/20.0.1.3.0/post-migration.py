# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Carry the classification added in this version to live accounts.

Same job as the script of 16.0.2.9.0, run again because this version ships new
tags (cash flow activity, value added distribution and the adjustments the
indirect cash flow statement adds back). A database that stopped at the
previous version got the tags that existed then and would never see these.
The script is idempotent: it only adds what is missing.

Odoo 18 has no `account.account.template`: the account CSVs the chart load
parses are the source of truth. The template to account mapping is the
`ir.model.data` the chart load creates, named `{company_id}_{template key}`,
with the module of the chart module that shipped the CSV (`account` for the
core utility accounts, `l10n_br_coa` and its chart flavors for ours). That is
the same path the core uses to know which account came from which template,
so it works for any chart, not only the ones shipped by the OCA.

The mapping is read from the CSVs directly through `_parse_csv`, the very
parser `try_loading` uses: whatever a database would get on a fresh load is
exactly what this script replays on existing accounts.

The migration never removes an existing classification: whoever tagged an
account by hand keeps what they did.
"""

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# account xmlid -> tag xmlids, per chart flavor shipped by the OCA
TAGGED_ACCOUNTS_BY_TEMPLATE = {}


def _collect_tagged_accounts(env):
    installed_names = set(
        env["ir.module.module"].search([("state", "=", "installed")]).mapped("name")
    )
    for chart_module in (
        "l10n_br_coa_generic",
        "l10n_br_coa_simple",
    ):
        if chart_module not in installed_names:
            continue
        for template_code, mapping in (
            env["account.chart.template"]
            ._get_chart_template_mapping(get_all=True)
            .items()
        ):
            if mapping.get("module") != chart_module:
                continue
            account_data = env["account.chart.template"]._parse_csv(
                template_code, "account.account"
            )
            for key, vals in account_data.items():
                tags = vals.get("tag_ids") or []
                if isinstance(tags, str):
                    tags = [t for t in tags.split(",") if t]
                if tags:
                    TAGGED_ACCOUNTS_BY_TEMPLATE[f"{chart_module}.{key}"] = tags


@openupgrade.migrate()
def migrate(env, version):
    _collect_tagged_accounts(env)
    if not TAGGED_ACCOUNTS_BY_TEMPLATE:
        _logger.info(
            "l10n_br_coa: no installed Brazilian chart flavor ships tagged"
            " accounts; nothing to carry over"
        )
        return

    # {template xmlid: tag ids} resolved against the tag records
    tags_by_xmlid = {}
    for account_xmlid, tag_xmlids in TAGGED_ACCOUNTS_BY_TEMPLATE.items():
        tag_ids = []
        for tag_xmlid in tag_xmlids:
            tag = env.ref(tag_xmlid, raise_if_not_found=False)
            if tag:
                tag_ids.append(tag.id)
        if tag_ids:
            tags_by_xmlid[account_xmlid] = tag_ids
    if not tags_by_xmlid:
        return

    # the chart load names the account mapping `{company_id}_{template key}`;
    # the leading module segment of the template xmlid is not part of it, so
    # index by the `{company_id}_{key}` suffix
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
