# Copyright (C) 2019 - Raphaël Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


def post_init_hook(env):
    """Allow to use demo main_company for Brazilian fiscal operations"""

    # "br_oca_generic" is only registered in _get_chart_template_mapping() when
    # l10n_br_coa_generic is installed. l10n_br_account doesn't depend on it, so
    # fall back to "generic_coa" when it's not there to avoid leaving demo
    # companies with an unresolvable chart_template (breaks mrp_account's
    # post_init_hook and other chart-template lookups).
    coa_generic_module = env.ref(
        "base.module_l10n_br_coa_generic", raise_if_not_found=False
    )
    coa_generic_installed = bool(
        coa_generic_module and coa_generic_module.state == "installed"
    )

    ChartTemplate = env["account.chart.template"]

    def _load_generic_coa_fallback(company):
        # fallback to generic_coa to make tests pass
        # FIXME tests should not depend on demo companies anymore!
        # Don't pre-set company.chart_template here: try_loading() only
        # actually (re)loads the chart's accounts when template_code differs
        # from the company's *current* chart_template value. try_loading()
        # itself sets the field once loading is done.
        ChartTemplate.try_loading("generic_coa", company, install_demo=True)
        ChartTemplate.load_fiscal_taxes([company])
        company.currency_id = env.ref("base.BRL")

    demo_simple = env.ref(
        "l10n_br_base.empresa_simples_nacional", raise_if_not_found=False
    )
    if demo_simple:
        # "br_oca_simple" is not implemented yet, generic_coa is the only
        # option for this demo company.
        _load_generic_coa_fallback(demo_simple)

    demo_lp = env.ref("l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False)
    if demo_lp:
        if coa_generic_installed:
            demo_lp.chart_template = "br_oca_generic"
        else:
            _load_generic_coa_fallback(demo_lp)

    if env.ref("base.module_l10n_br_account").demo:
        main_company = env.ref("base.main_company", raise_if_not_found=False)
        if main_company:
            # Set the company in Brazil BEFORE loading the fiscal taxes:
            # account.tax.country_id is a stored computed field (depends only
            # on company_id), so a tax keeps the country the company had at
            # creation time. Loading the taxes while the demo company is
            # still American would leave them with country_id = United
            # States and break account.move._validate_taxes_country (#5602).
            # account_fiscal_country_id has to be set explicitly: it is a
            # stored computed field that only takes company.country_id when
            # empty, and the demo company already has it set to the US.
            main_company.account_fiscal_country_id = env.ref("base.br").id
            main_company.country_id = env.ref("base.br").id
            main_company.state_id = env.ref("base.state_br_sp").id
            env["account.chart.template"].load_fiscal_taxes([main_company])
