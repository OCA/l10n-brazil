# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, Command, api, tools

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env.ref("base.module_l10n_br_tax_assessment").demo:
        load_posted_invoice_demo(env)


def load_posted_invoice_demo(env):
    """Post one purchase and one sale so the demo assessment has movement.

    Loaded from a hook because an invoice takes its journal and accounts from
    the active company, and the demo chart of accounts is itself loaded by a
    hook, so the journals may not exist yet when the manifest data loads.
    """
    company = env.ref("l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False)
    if not company:
        return

    journals = env["account.journal"].search(
        [("company_id", "=", company.id), ("type", "in", ("sale", "purchase"))]
    )
    if len(journals.mapped("type")) < 2:
        # A demo assessment reading zero looks like a broken tax engine.
        _logger.warning(
            "l10n_br_tax_assessment: no sale/purchase journal in %s, so the "
            "demo invoices were not posted and the demo assessment will have "
            "nothing to compute. Install l10n_br_coa_generic to load the chart "
            "of accounts of the demo companies.",
            company.display_name,
        )
        return

    user = env.user
    previous_company = user.company_id
    previous_companies = user.company_ids
    user.write(
        {
            "company_ids": [Command.set(env["res.company"].search([]).ids)],
            "company_id": company.id,
        }
    )
    try:
        tools.convert_file(
            env.cr,
            "l10n_br_tax_assessment",
            "demo/account_invoice_demo.xml",
            None,
            mode="init",
            noupdate=True,
            kind="demo",
        )
    finally:
        # Modules installed next expect the main company to be the active one.
        user.write(
            {
                "company_id": previous_company.id,
                "company_ids": [Command.set(previous_companies.ids)],
            }
        )

    _configure_demo_closing_accounts(env, company)
    _recompute_demo_assessments(env)


def _configure_demo_closing_accounts(env, company):
    """Point each assessed group at the accounts its own taxes already use.

    The chart does not fill the payable and receivable accounts the closing
    entry needs, so they are read from the tax repartition lines.
    """
    groups = env["account.tax.group"].search([])
    for group in groups:
        group_in_company = group.with_company(company)
        if (
            group_in_company.property_tax_payable_account_id
            and group_in_company.property_tax_receivable_account_id
        ):
            continue
        taxes = env["account.tax"].search(
            [("tax_group_id", "=", group.id), ("company_id", "=", company.id)]
        )
        vals = {}
        payable = _repartition_account(taxes, "sale")
        receivable = _repartition_account(taxes, "purchase")
        if payable:
            vals["property_tax_payable_account_id"] = payable.id
        if receivable:
            vals["property_tax_receivable_account_id"] = receivable.id
        if len(vals) == 2:
            group_in_company.write(vals)


def _repartition_account(taxes, type_tax_use):
    """The account the tax of this kind posts to, ignoring counterparts."""
    for tax in taxes.filtered(lambda t: t.type_tax_use == type_tax_use):
        for line in tax.invoice_repartition_line_ids:
            if (
                line.repartition_type == "tax"
                and line.factor_percent > 0
                and line.account_id
            ):
                return line.account_id
    return None


def _recompute_demo_assessments(env):
    """Reassess the demo records: demo data loads before this hook runs."""
    demo_assessments = env["l10n_br_tax.assessment"].browse()
    for xmlid in (
        "l10n_br_tax_assessment.demo_assessment_icms",
        "l10n_br_tax_assessment.demo_assessment_ipi",
        "l10n_br_tax_assessment.demo_assessment_pis",
        "l10n_br_tax_assessment.demo_assessment_cofins",
    ):
        assessment = env.ref(xmlid, raise_if_not_found=False)
        if assessment:
            demo_assessments |= assessment
    # Manual adjustment lines survive: only the lines read from move lines are rebuilt.
    demo_assessments.action_compute()
