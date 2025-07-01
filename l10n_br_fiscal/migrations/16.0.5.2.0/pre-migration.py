# Copyright (C) 2025 - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Migration script that was missing in the related PR:
    # https://github.com/OCA/l10n-brazil/pull/3768
    xmlids_renames = [
        (
            "l10n_br_fiscal.tax_icmsfcp_2_regulation_pb_pb",
            "l10n_br_fiscal.tax_icmsfcp_2_regulation_pr_pr",
        ),
        (
            "l10n_br_fiscal.tax_icmsfcp_nt_regulation_pb_pb",
            "l10n_br_fiscal.tax_icmsfcp_2_regulation_pb_pb",
        ),
    ]
    openupgrade.rename_xmlids(env.cr, xmlids_renames)
