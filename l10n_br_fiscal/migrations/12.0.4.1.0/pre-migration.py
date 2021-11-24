# Copyright (C) 2021 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_xmlids_spec = [
    ("l10n_br_fiscal.tax_ipi_simples_nacional", "l10n_br_fiscal.tax_ipi_outros"),
    ("l10n_br_fiscal.tax_pis_simples_nacional", "l10n_br_fiscal.tax_pis_outros"),
    ("l10n_br_fiscal.tax_cofins_simples_nacional", "l10n_br_fiscal.tax_cofins_outros"),
]


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.rename_xmlids(env.cr, _xmlids_spec)
