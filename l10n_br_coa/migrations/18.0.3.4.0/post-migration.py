# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Add the deductible IBS/CBS taxes and the IS taxes to existing companies.

The chart template only reaches a company when the chart is loaded, so the
taxes this version added to `account.tax-br_oca.csv` never arrive in a
database where the chart was loaded before. Without the deductible IBS and
CBS taxes an operation that uses deductible taxes adds the IBS/CBS amount to
the receivable again, and the invoice total no longer matches the title.

For each company that has the Brazilian tax groups the script creates only
what is missing, by xmlid, and never touches a tax that already exists:

* a tax that somebody created by hand (the workaround that was in use) is
  kept as it is and only gets the xmlid, so the deductible tax is not applied
  twice. It is found by what it does (company, tax group, use and
  `deductible`), whatever its name and whatever xmlid it has (an export from
  the screen gives it `__export__`); only the xmlids of the chart itself mark
  a tax as not made by hand. Active taxes come first: an archived workaround
  is never adopted in place of an active one, and when there is only an
  archived one the chart tax is created and the log says which one was left
  alone. The name only reinforces, with a warning in the log, and only among
  the active taxes: the unique name rule of the taxes ignores archived ones,
  so an archived tax does not stop the chart tax from being created;
* the repartition accounts of the other taxes are not rewritten, only the
  ones of the taxes created here and of the plain IBS and CBS taxes that were
  shipped with no account at all (`only_tax_templates`).

Accounts that the new taxes need and the company does not have are the ones
the chart load would have given a new company: for the generic and simple
charts they are loaded from the chart template (same code and xmlid), and the
helper the chart load uses creates only what the chart does not have, with the
review suffix. The flavor and suffix come from the same rule as the chart load.
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
    """Full xmlid of the company record for a chart key, or None.

    The chart load names it `account.{company}_{key}`, while
    `load_fiscal_taxes` names it `l10n_br_coa.{company}_{key}`.
    """
    for module in ("account", "l10n_br_coa"):
        xmlid = f"{module}.{company.id}_{key}"
        if env.ref(xmlid, raise_if_not_found=False):
            return xmlid
    return None


def _has_br_tax_groups(env, company):
    return bool(_company_xmlid(env, company, "tax_group_ibs"))


def _tax_framework(env, company):
    """Tax framework of the company, read where the field may not exist yet.

    This migration of `l10n_br_coa` runs while the modules that depend on it
    are not loaded: `tax_framework` belongs to `l10n_br_fiscal`, so the
    registry has no such field here (and `getattr` would say "no framework"
    and pick the ITG codes for a company of the normal regime). The column is
    already in the database, so it is read from there.
    """
    if "tax_framework" in company._fields:
        return company.tax_framework
    if openupgrade.column_exists(env.cr, "res_company", "tax_framework"):
        env.cr.execute(
            "SELECT tax_framework FROM res_company WHERE id = %s", (company.id,)
        )
        return env.cr.fetchone()[0]
    return False


def _link_existing_tax(env, company, key, tax):
    """Give the xmlid the chart load would have given to the tax.

    The chart load of the Brazilian charts names it `account.<company>_<key>`;
    `load_fiscal_taxes` (Brazilian taxes added to another chart) names it
    `l10n_br_coa.<company>_<key>`.
    """
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
    """Warn when the adopted tax does not give the amount back as expected.

    A deductible tax needs a tax repartition line with a negative factor and
    an account. The tax is kept as it is, so the log is the only way to tell
    that it does not work as the chart tax would.
    """
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
    """True when the record has an xmlid that the chart gave to the company.

    Those are `account.<company>_<key>` (chart load) and
    `l10n_br_coa.<company>_<key>` (`load_fiscal_taxes`). Any other xmlid, such
    as the `__export__` one that an export from the screen creates, does not
    make a record part of the chart.
    """
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
    """Tax somebody created for the same job as the one the chart adds.

    The match is by what the tax does (company, tax group, use and
    `deductible`), not by name: the workaround that was in use had any name
    ("IBS Dedutível", "IBS Saída Dedutível"...). The name only reinforces: a
    tax with the very same name has to be reused anyway, because the name is
    unique per company and use.

    Only active taxes are adopted. An archived tax is never adopted, not even
    when it has the name of the chart tax: the unique name rule of the taxes
    (`_constrains_name`) looks only at active taxes, so the chart tax can be
    created beside it, and adopting it would leave the company with no active
    deductible tax. The archived ones are reported in the log.
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
        # A tax that already is a record of the chart is not a tax made by
        # hand.
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
    by_name = env["account.tax"].search(
        [
            ("company_id", "=", company.id),
            ("type_tax_use", "=", vals["type_tax_use"]),
            ("name", "=", vals["name"]),
        ],
        order="id",
        limit=1,
    )
    if by_name:
        _logger.warning(
            "l10n_br_coa: company %s: the tax %r (id %s, %s) was matched by "
            "name only; its group, use or deductible flag are not the ones of "
            "the chart tax. Check it.",
            company.name,
            by_name.name,
            by_name.id,
            "active",
        )
    return by_name


def _load_missing_plan_accounts(env, company, chart, templates, flavor):
    """Create the chart accounts of the tax accounts that the company lacks.

    A chart load takes the account from the chart template, with its own
    code, name, type and tags. A company loaded before this version has not
    got the accounts the new CSV added to the chart, and the helper would
    create them with the review suffix: the same account would have a code
    for new companies and another one for this one. Load them from the chart
    data, like the chart load does (same record, same xmlid).
    """
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
    """Give the new records the module `load_fiscal_taxes` would have used.

    `_load_data` names what it creates `account.<company>_<key>`. On a chart
    that is not Brazilian the Brazilian taxes come from `load_fiscal_taxes`,
    which names them `l10n_br_coa.<company>_<key>`: the xmlids of the chart
    module are not left in the `account` namespace.
    """
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


def _migrate_company(env, company):
    chart = env["account.chart.template"].with_company(company)
    group_data = chart._get_br_oca_tax_group_data()
    tax_data = chart._get_br_oca_tax_data()

    data = {}
    new_groups = {
        key: group_data[key]
        for key in NEW_TAX_GROUPS
        if key in group_data and not _company_xmlid(env, company, key)
    }
    if new_groups:
        data["account.tax.group"] = new_groups

    new_taxes = {}
    kept_by_hand = 0
    for key in NEW_TAXES:
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
    for key in TAXES_WITHOUT_ACCOUNT:
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


def migrate_companies(env):
    for company in env["res.company"].with_context(active_test=False).search([]):
        if not _has_br_tax_groups(env, company):
            continue
        _migrate_company(env, company.with_company(company))


@openupgrade.migrate()
def migrate(env, version):
    migrate_companies(env)
