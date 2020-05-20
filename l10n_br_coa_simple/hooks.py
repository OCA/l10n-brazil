# Copyright (C) 2020 - Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Relate fiscal taxes to account taxes."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env['ir.module.module'].search_count([
        ('name', '=', 'l10n_br_account'),
        ('state', '=', 'installed'),
    ]):
        from odoo.addons.l10n_br_account.hooks import load_fiscal_taxes
        load_fiscal_taxes(env, env.ref(
            'l10n_br_coa_simple.l10n_br_coa_simple_chart_template'))
