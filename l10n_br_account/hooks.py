# Copyright (C) 2019 - Raphaël Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Relate fiscal taxes to account taxes."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    l10n_br_coa_charts = env["account.chart.template"].search(
        [("parent_id", "=", env.ref("l10n_br_coa.l10n_br_coa_template").id)]
    )

    for l10n_br_coa_chart in l10n_br_coa_charts:
        l10n_br_coa_chart.load_fiscal_taxes()
