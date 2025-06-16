# Copyright 2023 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from pathlib import Path

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Import demo SPED file"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env.ref("base.module_l10n_br_sped_ecd").demo:
        parent_dir = Path(__file__).resolve().parent
        file_path = parent_dir / "demo" / "demo_ecd.txt"
        env["l10n_br_sped.mixin"]._flush_registers("ecd")
        env["l10n_br_sped.mixin"]._import_file(file_path, "ecd")
