# Copyright (C) 2020 - Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, tools, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    coa_simple_tmpl = env.ref(
        'l10n_br_coa_simple.l10n_br_coa_simple_chart_template')
    if env['ir.module.module'].search_count([
        ('name', '=', 'l10n_br_account'),
        ('state', '=', 'installed'),
    ]):
        from odoo.addons.l10n_br_account.hooks import load_fiscal_taxes
        # Relate fiscal taxes to account taxes.
        load_fiscal_taxes(env, coa_simple_tmpl)

    # Load COA to Demo Company
    if not tools.config.get('without_demo'):
        env.user.company_id = env.ref(
            'l10n_br_fiscal.empresa_simples_nacional')
        coa_simple_tmpl.try_loading_for_current_company()
