# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Carry the account classification from the chart templates to live accounts.

As of Odoo 17.0 the CoA no longer uses ``account.account.template``. Tags
live on the chart CSV (``tag_ids`` or the OCA ``tag_ids:id`` column) and
only reach ``account.account`` when the chart is loaded into a company.
Updating the module updates the template files, not the accounts already
created, and the reports would read zero because they select by
classification.

The template to account mapping is the ``ir.model.data`` the chart load
creates, named ``{company_id}_{template xmlid}``. That is the same path the
core uses to know which account came from which template, so it works for any
chart, not only the two shipped by the OCA.

The migration never removes an existing classification: whoever tagged an
account by hand keeps what they did.
"""

import csv
import logging

from openupgradelib import openupgrade

from odoo.tools.misc import file_open

_logger = logging.getLogger(__name__)


def _tag_xmlids_from_row(row):
    raw = row.get("tag_ids") or row.get("tag_ids:id") or ""
    return [xmlid.strip() for xmlid in raw.split(",") if xmlid.strip()]


def _account_tags_from_chart(env, template_code):
    """Return {account template xmlid: tag recordset} for a chart template."""
    chart = env["account.chart.template"]
    mapping = chart._get_chart_template_mapping(get_all=True)
    tags_by_xmlid = {}
    for code in reversed(chart._get_parent_template(template_code)):
        template_info = mapping.get(code)
        if not template_info:
            continue
        path = f"{template_info['module']}/data/template/account.account-{code}.csv"
        try:
            with file_open(path, mode="r") as csv_file:
                for row in csv.DictReader(csv_file):
                    account_xmlid = row.get("id")
                    tag_xmlids = _tag_xmlids_from_row(row)
                    if not account_xmlid or not tag_xmlids:
                        continue
                    tags = env["account.account.tag"]
                    for tag_xmlid in tag_xmlids:
                        tag = env.ref(tag_xmlid, raise_if_not_found=False)
                        if tag:
                            tags |= tag
                    if tags:
                        tags_by_xmlid[account_xmlid] = tags
        except FileNotFoundError:
            _logger.debug("No account CSV for chart template %s (%s)", code, path)
    return tags_by_xmlid


@openupgrade.migrate()
def migrate(env, version):
    companies = env["res.company"].search([("chart_template", "!=", False)])
    if not companies:
        return

    updated = 0
    for company in companies:
        tags_by_xmlid = _account_tags_from_chart(env, company.chart_template)
        if not tags_by_xmlid:
            continue

        suffix_map = {
            f"{company.id}_{account_xmlid}": tags
            for account_xmlid, tags in tags_by_xmlid.items()
        }
        account_data = env["ir.model.data"].search(
            [
                ("model", "=", "account.account"),
                ("name", "in", list(suffix_map)),
            ]
        )
        for data in account_data:
            account = env["account.account"].browse(data.res_id).exists()
            if not account:
                continue
            missing = suffix_map[data.name] - account.tag_ids
            if missing:
                account.write({"tag_ids": [(4, tag.id) for tag in missing]})
                updated += 1

    _logger.info("l10n_br_coa: classification applied to %s existing accounts", updated)
