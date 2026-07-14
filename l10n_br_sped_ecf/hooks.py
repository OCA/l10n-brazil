# Copyright 2023 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).


def post_init_hook(env):
    """Import demo SPED file."""
    if env.ref("base.module_l10n_br_sped_ecf").demo:
        # FIXME: the current demo ECF file is buggy; demo import disabled.
        # parent_dir = Path(__file__).resolve().parent
        # file_path = parent_dir / "demo" / "demo_efc.txt"
        # env["l10n_br_sped.mixin"]._import_file(file_path, "ecf")
        pass
