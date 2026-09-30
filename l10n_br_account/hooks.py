# Copyright (C) 2019 - Raphaël Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

# Brazilian demo companies of l10n_br_base: they are created without any
# chart of accounts and are meant to be used to test the Brazilian
# localization (demo/preview databases, tests of the modules depending on
# this one, ...).
BR_DEMO_COMPANY_XMLIDS = (
    "l10n_br_base.empresa_lucro_presumido",
    "l10n_br_base.empresa_simples_nacional",
)


def post_init_hook(env):
    """Make the Brazilian demo companies usable.

    Load the generic chart of accounts of Odoo on the Brazilian demo
    companies which have no accounting data yet, together with the Brazilian
    fiscal taxes and the BRL currency, so that they can really post Brazilian
    invoices.

    The Brazilian chart modules (l10n_br_coa_generic, l10n_br_coa_simple) are
    optional: when a Brazilian chart package is installed, the companies keep
    the chart they are configured with and only the fiscal taxes are completed.
    """
    chart_template = env["account.chart.template"]
    for xmlid in BR_DEMO_COMPANY_XMLIDS:
        company = env.ref(xmlid, raise_if_not_found=False)
        if not company:
            continue
        has_journal = env["account.journal"].search_count(
            [("company_id", "=", company.id)]
        )
        if not has_journal:
            # fallback to generic_coa: the demo companies must be able to post
            # invoices even when no Brazilian chart package is installed
            chart_template.try_loading("generic_coa", company, install_demo=True)
        chart_template.load_fiscal_taxes([company])
        company.currency_id = env.ref("base.BRL")

    if env.ref("base.module_l10n_br_account").demo:
        main_company = env.ref("base.main_company", raise_if_not_found=False)
        if main_company:
            chart_template.load_fiscal_taxes([main_company])

            # now that generic_coa demo data were loaded for main_company,
            # we can set it in Brazil:
            main_company.country_id = env.ref("base.br").id
            main_company.state_id = env.ref("base.state_br_sp").id
