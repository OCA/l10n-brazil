from . import models


def install_chart_template(env, chart_template_id, desired_tax_frameworks):
    """Install chart template in desired companies"""
    original_company_id = env.user.company_id
    for company_id in env["res.company"].search([]):
        country_code =company_id.country_id.code
        if country_code and country_code.upper() == "BR" and \
                company_id.tax_framework in desired_tax_frameworks:
            if company_id.chart_template_id != chart_template_id:
                env.user.company_ids |= company_id
                env.user.company_id = company_id
                chart_template_id.load_for_current_company(15.0, 15.0)

        if env['ir.module.module'].search_count([
            ('name', '=', 'l10n_br_account'),
            ('state', '=', 'installed'),
        ]):
            from odoo.addons.l10n_br_account.hooks import load_fiscal_taxes
            load_fiscal_taxes(env, chart_template_id)

    env.user.company_id = original_company_id
