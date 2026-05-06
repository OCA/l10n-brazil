# Copyright (C) 2019 - Raphaël Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tools import mute_logger


def post_init_hook(env):
    """Allow to use demo main_company for Brazilian fiscal operations"""

    br_demo_companies = []
    demo_simple = env.ref(
        "l10n_br_base.empresa_simples_nacional", raise_if_not_found=False
    )
    if demo_simple:
        demo_simple.chart_template = "generic_coa"  # "br_oca_simple"
        br_demo_companies.append(demo_simple)
    demo_lp = env.ref("l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False)
    if demo_lp:
        demo_lp.chart_template = "br_oca_generic"
        br_demo_companies.append(demo_lp)

    for company in env["res.company"].with_context(active_test=False).search([]):
        if "br_oca" in env["account.chart.template"]._get_parent_template(
            company.chart_template
        ):
            if company in br_demo_companies:
                # fallback to generic_coa to make tests pass
                # FIXME tests should not depend on demo companies anymore!
                with mute_logger("odoo.addons.account.models.chart_template"):
                    env["account.chart.template"].try_loading("generic_coa", company)
                env["account.chart.template"].load_fiscal_taxes([company])
                company.currency_id = env.ref("base.BRL")

    if env.ref("base.module_l10n_br_account").demo:
        main_company = env.ref("base.main_company", raise_if_not_found=False)
        if main_company:
            env["account.chart.template"].load_fiscal_taxes([main_company])

            # now that generic_coa demo data were loaded for main_company,
            # we can set it in Brazil:
            env.ref("base.main_company").country_id = env.ref("base.br").id
            env.ref("base.main_company").state_id = env.ref("base.state_br_sp").id
