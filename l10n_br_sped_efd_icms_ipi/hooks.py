# Copyright 2023 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from os import path

from odoo import SUPERUSER_ID, api

from odoo.addons import l10n_br_sped_efd_icms_ipi


def post_init_hook(cr, registry):
    """Import demo SPED file"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.cr.execute(
        "select demo from ir_module_module where name='l10n_br_sped_efd_icms_ipi';"
    )
    if env.cr.fetchone()[0]:
        demo_path = path.join(l10n_br_sped_efd_icms_ipi.__path__[0], "demo")
        file_path = path.join(demo_path, "demo_efd_icms_ipi.txt")
        env["l10n_br_sped.mixin"]._flush_registers("efd_icms_ipi")
        env["l10n_br_sped.mixin"]._import_file(file_path, "efd_icms_ipi")
