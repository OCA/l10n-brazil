# Copyright (C) 2020 - Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    coa_complete_tmpl = env.ref(
        'l10n_br_coa_complete.l10n_br_coa_complete_template')
    if env['ir.module.module'].search_count([
        ('name', '=', 'l10n_br_account'),
        ('state', '=', 'installed'),
    ]):
        from odoo.addons.l10n_br_account.hooks import load_fiscal_taxes
        # Relate fiscal taxes to account taxes.
        load_fiscal_taxes(env, coa_complete_tmpl)

    # # Load COA to Demo Company
    # if not tools.config.get('without_demo'):
    #     user_admin = env.ref('base.user_admin')
    #     company = env.ref(
    #         'l10n_br_base.empresa_lucro_presumido', raise_if_not_found=False)
    #     if company:
    #         user_admin.company_id = company
    #         coa_complete_tmpl.sudo(
    #             user=user_admin.id).try_loading_for_current_company()
    #         user_admin.company_id = env.ref('base.main_company')
