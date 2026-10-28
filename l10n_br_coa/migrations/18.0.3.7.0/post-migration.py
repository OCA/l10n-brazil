# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Add the deductible IBS/CBS taxes and the IS taxes to existing companies.

Only what is missing is created, by xmlid. A tax made by hand is adopted (it
only gets the xmlid) so the deductible tax is not applied twice.
"""

import logging

from openupgradelib import openupgrade

from odoo import Command

_logger = logging.getLogger(__name__)

NEW_TAX_GROUPS = ["tax_group_is"]
NEW_TAXES = [
    "tax_template_out_ibs_deductible",
    "tax_template_in_ibs_deductible",
    "tax_template_out_cbs_deductible",
    "tax_template_in_cbs_deductible",
    "tax_template_out_is",
    "tax_template_in_is",
    "tax_template_out_is_deductible",
    "tax_template_in_is_deductible",
]
# Taxes that 18.0 shipped without any account on the repartition lines.
TAXES_WITHOUT_ACCOUNT = [
    "tax_template_out_ibs",
    "tax_template_in_ibs",
    "tax_template_out_cbs",
    "tax_template_in_cbs",
]
# Charts whose accounts the company shares with the chart template.
PLAN_CHARTS = ("br_oca_generic", "br_oca_simple")
BR_CHARTS = PLAN_CHARTS + ("br_oca",)


def _company_xmlid(env, company, key):
    """Full xmlid of the company record for a chart key, or None."""
    for module in ("account", "l10n_br_coa"):
        xmlid = f"{module}.{company.id}_{key}"
        if env.ref(xmlid, raise_if_not_found=False):
            return xmlid
    return None


def _has_br_tax_groups(env, company):
    return bool(_company_xmlid(env, company, "tax_group_ibs"))


def _tax_framework(env, company):
    """Tax framework, read from the column (the field is not loaded here)."""
    if "tax_framework" in company._fields:
        return company.tax_framework
    if openupgrade.column_exists(env.cr, "res_company", "tax_framework"):
        env.cr.execute(
            "SELECT tax_framework FROM res_company WHERE id = %s", (company.id,)
        )
        return env.cr.fetchone()[0]
    return False


def _link_existing_tax(env, company, key, tax):
    """Give the tax the xmlid the chart load would have given it."""
    module = "account" if company.chart_template in BR_CHARTS else "l10n_br_coa"
    env["ir.model.data"].sudo().create(
        {
            "name": f"{company.id}_{key}",
            "module": module,
            "model": "account.tax",
            "res_id": tax.id,
            "noupdate": True,
        }
    )


def _warn_if_not_deductible(company, tax):
    """Warn when the adopted tax has no negative factor or no account."""
    lines = (
        tax.invoice_repartition_line_ids | tax.refund_repartition_line_ids
    ).filtered(lambda line: line.repartition_type == "tax")
    if not any(line.factor_percent < 0 for line in lines):
        _logger.warning(
            "l10n_br_coa: company %s: the tax %r (id %s) was kept as the chart "
            "tax but has no repartition line with a negative factor. Check it.",
            company.name,
            tax.name,
            tax.id,
        )
    if not lines.account_id:
        _logger.warning(
            "l10n_br_coa: company %s: the tax %r (id %s) was kept as the chart "
            "tax but has no account in its repartition lines. Check it.",
            company.name,
            tax.name,
            tax.id,
        )


def _is_chart_record(env, company, record):
    """True when the record has an xmlid that the chart gave to the company."""
    return bool(
        env["ir.model.data"]
        .sudo()
        .search_count(
            [
                ("model", "=", record._name),
                ("res_id", "=", record.id),
                ("module", "in", ("account", "l10n_br_coa")),
                ("name", "=like", f"{company.id}\\_%"),
            ]
        )
    )


def _find_tax_made_by_hand(env, company, vals):
    """Active tax made by hand for the same job as the chart tax.

    Matched by company, group, use and `deductible`; archived taxes are never
    adopted, only reported. The name only reinforces, with a warning.
    """
    Tax = env["account.tax"].with_context(active_test=False)
    group = env.ref(vals["tax_group_id"], raise_if_not_found=False)
    domain = [
        ("company_id", "=", company.id),
        ("type_tax_use", "=", vals["type_tax_use"]),
        ("deductible", "=", vals.get("deductible", False)),
    ]
    if group:
        by_structure = Tax.search(
            domain + [("tax_group_id", "=", group.id)], order="active desc, id"
        )
        by_structure = by_structure.filtered(
            lambda tax: not _is_chart_record(env, company, tax)
        )
        active = by_structure.filtered("active")
        if active:
            if len(active) > 1:
                _logger.warning(
                    "l10n_br_coa: company %s has %s active taxes of group %s, "
                    "use %s and deductible=%s; %s (id %s) is kept as the chart "
                    "tax %r",
                    company.name,
                    len(active),
                    group.name,
                    vals["type_tax_use"],
                    vals.get("deductible", False),
                    active[0].name,
                    active[0].id,
                    vals["name"],
                )
            return active[0]
        if by_structure:
            _logger.warning(
                "l10n_br_coa: company %s has only archived taxes of group %s, "
                "use %s and deductible=%s (%s); they are left as they are and "
                "the chart tax %r is created",
                company.name,
                group.name,
                vals["type_tax_use"],
                vals.get("deductible", False),
                ", ".join(f"{tax.name} (id {tax.id})" for tax in by_structure),
                vals["name"],
            )
    # Explicit: an archived company runs with `active_test=False`.
    by_name = (
        env["account.tax"]
        .with_context(active_test=True)
        .search(
            [
                ("company_id", "=", company.id),
                ("type_tax_use", "=", vals["type_tax_use"]),
                ("name", "=", vals["name"]),
            ],
            order="id",
            limit=1,
        )
    )
    if by_name:
        _logger.warning(
            "l10n_br_coa: company %s: the tax %r (id %s) was matched by "
            "name only; its group, use or deductible flag are not the ones of "
            "the chart tax. Check it.",
            company.name,
            by_name.name,
            by_name.id,
        )
    return by_name


def _load_missing_plan_accounts(env, company, chart, templates, flavor):
    """Create the chart accounts of the tax accounts that the company lacks."""
    if company.chart_template not in PLAN_CHARTS or company.parent_id:
        # A branch uses the accounts of the parent company.
        return
    _templates, accounts = chart._get_default_tax_accounts(templates)
    index = 0 if flavor == "cfc" else 1
    codes = {value[index] for value in accounts.values() if value[index]}
    Account = env["account.account"].with_company(company)
    plan = chart._get_chart_template_data(company.chart_template).get(
        "account.account", {}
    )
    missing = {}
    for key, vals in plan.items():
        code = vals.get("code")
        if code not in codes:
            continue
        if Account.search_count(
            [("code", "=", code), ("company_ids", "parent_of", company.id)]
        ):
            continue
        missing[key] = dict(vals, company_ids=[Command.link(company.id)])
    if missing:
        chart._load_data({"account.account": missing})
        env.flush_all()
    return missing


def _name_like_load_fiscal_taxes(env, company, data):
    """Name the new records in `l10n_br_coa`, as `load_fiscal_taxes` does."""
    if company.chart_template in BR_CHARTS:
        return
    names = [f"{company.id}_{key}" for keys in data.values() for key in keys]
    records = (
        env["ir.model.data"]
        .sudo()
        .search(
            [
                ("module", "=", "account"),
                ("name", "in", names),
                ("model", "in", list(data)),
            ]
        )
    )
    records.write({"module": "l10n_br_coa"})


def _migrate_company(
    env, company, tax_groups=None, taxes=None, taxes_without_account=None
):
    """Create what the company lacks; a later migration passes its own lists."""
    if tax_groups is None:
        tax_groups = NEW_TAX_GROUPS
    if taxes is None:
        taxes = NEW_TAXES
    if taxes_without_account is None:
        taxes_without_account = TAXES_WITHOUT_ACCOUNT
    env = company.env
    chart = env["account.chart.template"].with_company(company)
    group_data = chart._get_br_oca_tax_group_data()
    tax_data = chart._get_br_oca_tax_data()

    data = {}
    new_groups = {
        key: group_data[key]
        for key in tax_groups
        if key in group_data and not _company_xmlid(env, company, key)
    }
    if new_groups:
        data["account.tax.group"] = new_groups

    new_taxes = {}
    kept_by_hand = 0
    for key in taxes:
        if key not in tax_data or _company_xmlid(env, company, key):
            continue
        vals = dict(tax_data[key])
        # A group that already exists may carry either module in its xmlid.
        vals["tax_group_id"] = (
            _company_xmlid(env, company, vals["tax_group_id"]) or vals["tax_group_id"]
        )
        by_hand = _find_tax_made_by_hand(env, company, vals)
        if by_hand:
            _link_existing_tax(env, company, key, by_hand)
            _warn_if_not_deductible(company, by_hand)
            kept_by_hand += 1
            continue
        new_taxes[key] = vals
    if new_taxes:
        data["account.tax"] = new_taxes

    if data:
        chart._load_data(data)
        env.flush_all()
        _name_like_load_fiscal_taxes(env, company, data)
    to_populate = list(new_taxes)
    for key in taxes_without_account:
        xmlid = _company_xmlid(env, company, key)
        tax = env.ref(xmlid) if xmlid else env["account.tax"]
        lines = (
            tax.invoice_repartition_line_ids | tax.refund_repartition_line_ids
        ).filtered(lambda line: line.repartition_type == "tax")
        if lines and not lines.account_id:
            to_populate.append(key)
    if to_populate:
        templates = [f"l10n_br_coa.{key}" for key in to_populate]
        flavor, suffix = chart._get_br_tax_accounts_params(
            company, tax_framework=_tax_framework(env, company)
        )
        _load_missing_plan_accounts(env, company, chart, templates, flavor)
        chart._populate_default_br_tax_accounts(
            company,
            flavor=flavor,
            review_suffix=suffix,
            only_tax_templates=templates,
        )
    _logger.info(
        "l10n_br_coa: company %s: %s tax group(s) and %s tax(es) created, "
        "%s existing tax(es) kept, accounts set on %s tax(es)",
        company.name,
        len(new_groups),
        len(new_taxes),
        kept_by_hand,
        len(to_populate),
    )


def migrate_companies(env, **lists):
    """Migrate every company with the Brazilian tax groups, archived or not.

    `lists` (`tax_groups`, `taxes`, `taxes_without_account`) goes to
    `_migrate_company`.
    """
    for company in env["res.company"].with_context(active_test=False).search([]):
        if not _has_br_tax_groups(env, company):
            continue
        if not company.active:
            _logger.info(
                "l10n_br_coa: company %s is archived and is migrated anyway",
                company.name,
            )
            company = company.with_env(env).with_context(active_test=False)
        else:
            company = company.with_env(env)
        _migrate_company(env, company.with_company(company), **lists)


@openupgrade.migrate()
def migrate(env, version):
    migrate_companies(env)
