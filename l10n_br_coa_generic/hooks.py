# Copyright (C) 2020 - Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Relate fiscal taxes to account taxes."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    chart_template_id = env.ref(
        'l10n_br_coa_generic.l10n_br_coa_generic_template')
    original_company_id = env.user.company_id
    for company_id in env["res.company"].search([]):
        country_code =company_id.country_id.code
        if country_code and country_code.upper() == "BR" and \
                company_id.tax_framework == '3':
            if company_id.chart_template_id != chart_template_id:
                env.user.company_ids |= company_id
                env.user.company_id = company_id
                chart_template_id.load_for_current_company(15.0, 15.0)

        if env['ir.module.module'].search_count([
            ('name', '=', 'l10n_br_account'),
            ('state', '=', 'installed'),
        ]):
            from odoo.addons.l10n_br_account.hooks import load_fiscal_taxes
            load_fiscal_taxes(env, env.ref(
                'l10n_br_coa_generic.l10n_br_coa_generic_template'))

    env.user.company_id = original_company_id
