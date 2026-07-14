# Copyright 2023 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from pathlib import Path


def post_init_hook(env):
    """Import demo SPED file"""
    if env.ref("base.module_l10n_br_sped_efd_pis_cofins").demo:
        parent_dir = Path(__file__).resolve().parent
        file_path = parent_dir / "demo" / "demo_efd_pis_cofins_multi.txt"
        env["l10n_br_sped.mixin"]._flush_registers("efd_pis_cofins")
        env["l10n_br_sped.mixin"]._import_file(file_path, "efd_pis_cofins")
