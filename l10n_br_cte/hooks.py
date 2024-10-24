# Copyright (C) 2019-2020 - Raphael Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["cte.40.tcte_infcte"]._register_hook()
    # hooks.register_hook(
    #     env,
    #     "l10n_br_cte",
    #     "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00",
    # )
