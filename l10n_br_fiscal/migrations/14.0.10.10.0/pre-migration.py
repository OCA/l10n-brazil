# Copyright (C) 2023 - Ygor Carvalho - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_field_renames = [
    (
        "res.company",
        "res_company",
        "nfe_transmission",
        "edoc_transmission",
    ),
]


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.rename_fields(env, _field_renames)
