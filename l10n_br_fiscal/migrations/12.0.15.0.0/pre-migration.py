# Copyright (C) 2021 - Raphaêl Valyi - Akretion
# License AGPL-3.0 or later (
# http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_column_renames = {
    # l10n_br_fiscal/models/cest.py
    # l10n_br_fiscal/models/ncm_cest.py
    "fiscal_cest_ncm_rel": [
        ("l10n_br_fiscal_ncm_id", "ncm_id"),
        ("l10n_br_fiscal_cest_id", "cest_id"),
    ],
    # l10n_br_fiscal/models/nbm.py
    # l10n_br_fiscal/models/ncm_nbm.py
    "fiscal_nbm_ncm_rel": [
        ("l10n_br_fiscal_ncm_id", "ncm_id"),
        ("l10n_br_fiscal_nbm_id", "nbm_id"),
    ],
    # l10n_br_fiscal/models/simplified_tax.py
    "fiscal_simplified_tax_cnae_rel": [
        ("l10n_br_fiscal_simplified_tax_id", "simplified_tax_id"),
        ("l10n_br_fiscal_cnae_id", "cnae_id"),
    ],
    # l10n_br_fiscal/models/ncm_tax_pis_cofins.py
    # l10n_br_fiscal/models/tax_pis_cofins.py
    "fiscal_pis_cofins_ncm_rel": [
        ("l10n_br_fiscal_ncm_id", "ncm_id"),
        ("l10n_br_fiscal_tax_pis_cofins_id", "piscofins_id"),
    ],
    # l10n_br_fiscal/models/res_company.py
    "res_company_fiscal_cnae_rel": [
        ("res_company_id", "company_id"),
        ("l10n_br_fiscal_cnae_id", "cnae_id"),
    ],
    # l10n_br_fiscal/models/tax_definition.py
    "tax_definition_state_to_rel": [
        ("l10n_br_fiscal_tax_definition_id", "tax_definition_id"),
        ("res_country_state_id", "state_id"),
    ],
    # l10n_br_fiscal/models/tax_definition.py
    "tax_definition_ncm_rel": [
        ("l10n_br_fiscal_tax_definition_id", "tax_definition_id"),
        ("l10n_br_fiscal_ncm_id", "ncm_id"),
    ],
    # l10n_br_fiscal/models/tax_definition.py
    "tax_definition_cest_rel": [
        ("l10n_br_fiscal_tax_definition_id", "tax_definition_id"),
        ("l10n_br_fiscal_cest_id", "cest_id"),
    ],
    # l10n_br_fiscal/models/tax_definition.py
    "tax_definition_nbm_rel": [
        ("l10n_br_fiscal_tax_definition_id", "tax_definition_id"),
        ("l10n_br_fiscal_nbm_id", "nbm_id"),
    ],
    # l10n_br_fiscal/models/tax_definition.py
    "tax_definition_product_rel": [
        ("l10n_br_fiscal_tax_definition_id", "tax_definition_id"),
        ("product_product_id", "product_id"),  # TODO not with product_template??
    ],
}


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.rename_columns(env.cr, _column_renames)
