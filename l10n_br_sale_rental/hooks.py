# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Warehouses that already rent get the fiscal rental rules."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["stock.warehouse"].search(
        [("rental_allowed", "=", True)]
    )._l10n_br_set_rental_rules()
