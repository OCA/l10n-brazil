# Copyright (C) 2020 - Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api
from odoo.addons.l10n_br_coa import install_chart_template


def post_init_hook(cr, registry):
    """Relate fiscal taxes to account taxes."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    chart_template_id = env.ref(
        'l10n_br_coa_simple.l10n_br_coa_simple_chart_template')
    install_chart_template(env, chart_template_id, ['1', '2'])
