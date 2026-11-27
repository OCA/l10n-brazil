# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """The vendor bill of an imported fiscal document moved from the import wizard
    of this module to l10n_br_account_edi, which installs on its own with a new
    database but not when an existing one is updated: install it here, where the
    import of fiscal documents is in use (l10n_br_fiscal_edi is installed)."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    modules = env["ir.module.module"]
    if modules.search_count(
        [("name", "=", "l10n_br_fiscal_edi"), ("state", "=", "installed")]
    ):
        modules.search(
            [("name", "=", "l10n_br_account_edi"), ("state", "=", "uninstalled")]
        ).button_install()
