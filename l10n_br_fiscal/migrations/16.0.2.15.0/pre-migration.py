# Copyright 2025 Engenere - Antônio S. P. Neto.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    xmlids_renames = [
        (
            "l10n_br_fiscal.ncm_70200090_ P",
            "l10n_br_fiscal.ncm_70200090_P",
        ),
        (
            "l10n_br_fiscal.ncm_68159990_ P",
            "l10n_br_fiscal.ncm_68159990_P",
        ),
    ]
    openupgrade.rename_xmlids(env.cr, xmlids_renames)
