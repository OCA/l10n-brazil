# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, Command, api, tools

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    load_posted_invoice_demo(env)


def load_posted_invoice_demo(env):
    """Post one purchase and one sale so the demo assessment has movement.

    Loaded from a hook rather than from the manifest for two reasons. An
    invoice takes its journal and its accounts from the ACTIVE company, so it
    has to be created with the demo company active or the moves land in the
    wrong company's books, silently. And the chart of accounts of the demo
    company is itself loaded by a hook (`l10n_br_coa_generic`), so the journals
    these invoices need may not exist yet when this module installs.

    Both conditions are checked rather than assumed: no demo company means a
    database without demo data, and no journal means the chart was never
    loaded. In either case there is nothing to post and nothing to assess.
    """
    company = env.ref("l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False)
    if not company:
        return

    journals = env["account.journal"].search(
        [("company_id", "=", company.id), ("type", "in", ("sale", "purchase"))]
    )
    if len(journals.mapped("type")) < 2:
        # Without a chart there is no journal to post to. Say so out loud: a
        # demo assessment reading zero looks the same as a broken tax engine,
        # and that is the confusion this whole file exists to remove.
        _logger.warning(
            "l10n_br_tax_assessment: no sale/purchase journal in %s, so the "
            "demo invoices were not posted and the demo assessment will have "
            "nothing to compute. Install l10n_br_coa_generic to load the chart "
            "of accounts of the demo companies.",
            company.display_name,
        )
        return

    previous_company = env.user.company_id
    env.user.company_ids = [Command.set(env["res.company"].search([]).ids)]
    env.user.company_id = company
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
        # The modules installed next expect the main company to be the default
        # one; leaving another company active breaks their own demo.
        env.user.company_id = previous_company

    _configure_demo_closing_accounts(env, company)
    _recompute_demo_assessments(env)


def _configure_demo_closing_accounts(env, company):
    """Point each assessed group at the accounts its own taxes already use.

    Closing needs to know where the tax sits: `property_tax_payable_account_id`
    for what is owed and `property_tax_receivable_account_id` for what is
    recoverable. The chart never fills them, so `action_post` stops on a demo
    database asking for configuration, and the closing entry, which is the
    final artefact of the whole routine, cannot be shown at all.

    The accounts are read from the tax repartition instead of being named here.
    A sale tax posts into the account the tax is owed in and a purchase tax
    into the recoverable one, so the chart already answers the question; naming
    the codes in this file would only be a second, silent copy of that answer,
    wrong the day a chart changes.
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
    """The account the tax of this kind posts to, ignoring counterparts.

    The counterpart of a creditable input carries a negative repartition and
    posts to the cost account, not to the recoverable one, so reading it would
    point the closing entry at an expense account.
    """
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
    """Reassess the demo records now that there is movement to assess.

    Demo data is loaded BEFORE the post init hook, so the assessments computed
    themselves against an accounting that was still empty. They would sit at
    zero for good otherwise, which is precisely the state this module's demo
    is meant to stop showing.
    """
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
    # Only the lines read from the move lines are rebuilt; the manual
    # adjustments the demo carries survive, which is the whole point of
    # keeping them apart by `source`.
    demo_assessments.action_compute()
