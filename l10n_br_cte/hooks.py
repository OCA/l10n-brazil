# Copyright (C) 2019-2020 - Raphael Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import SUPERUSER_ID, api

from odoo.addons.spec_driven_model import hooks


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    hooks.register_hook(
        env,
        "l10n_br_cte",
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00",
    )

    hooks.post_init_hook(
        cr,
        registry,
        "l10n_br_cte",
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00",
    )
