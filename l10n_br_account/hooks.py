# Copyright (C) 2019 - Raphaël Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


def post_init_hook(env):
    """Inject Brazilian taxes in the CoA and related them to the account taxes."""

    br_demo_companies = [
        env.ref("l10n_br_base.empresa_simples_nacional"),
        env.ref("l10n_br_base.empresa_lucro_presumido"),
    ]
    todo_companies = []
    for company in env["res.company"].with_context(active_test=False).search([]):
        if "br_oca" in env["account.chart.template"]._get_parent_template(
            company.chart_template
        ):
            env["account.chart.template"].try_loading(company.chart_template, company)
            todo_companies.append(company)
        elif company in br_demo_companies:  # fallback to generic_coa
            env["account.chart.template"].try_loading("generic_coa", company)
            company.currency_id = env.ref("base.BRL")
            todo_companies.append(company)

    main_company = env.ref("base.main_company")
    if (
        main_company not in todo_companies
        and env.ref("base.module_l10n_br_account").demo
    ):
        todo_companies.append(main_company)
    env["account.chart.template"].load_fiscal_taxes(todo_companies)

    # now that generic_coa demo data were loaded for main_company, we can set it in Brazil:
    env.ref("base.main_company").country_id = env.ref("base.br").id
