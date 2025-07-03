# Copyright (C) 2025 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

_tables_renames = [
    # l10n_br_fiscal/models/operation.py: comment_ids
    (
        "l10n_br_fiscal_operation_comment_rel",
        "l10n_br_fiscal_comment_l10n_br_fiscal_operation_rel",
    ),
    # l10n_br_fiscal/models/operation_line.py: comment_ids
    (
        "l10n_br_fiscal_operation_line_comment_rel",
        "l10n_br_fiscal_comment_l10n_br_fiscal_operation_line_rel",
    ),
    # l10n_br_fiscal/models/res_company.py: cnae_secondary_ids
    ("res_company_fiscal_cnae_rel", "l10n_br_fiscal_cnae_res_company_rel"),
    # l10n_br_fiscal/models/document_mixin.py: comment_ids
    # (Abstract, assumes concrete l10n_br_fiscal.document)
    (
        "l10n_br_fiscal_document_mixin_comment_rel",
        "l10n_br_fiscal_comment_l10n_br_fiscal_document_rel",
    ),
    # l10n_br_fiscal/models/document_line_mixin.py: fiscal_tax_ids
    # (Abstract, assumes concrete l10n_br_fiscal.document.line)
    ("fiscal_tax_rel", "l10n_br_fiscal_document_line_l10n_br_fiscal_tax_rel"),
    # l10n_br_fiscal/models/document_line_mixin.py: comment_ids
    # (Abstract, assumes concrete l10n_br_fiscal.document.line)
    (
        "l10n_br_fiscal_document_line_mixin_comment_rel",
        "l10n_br_fiscal_comment_l10n_br_fiscal_document_line_rel",
    ),
    # l10n_br_fiscal/models/nbm.py: ncm_ids
    ("fiscal_nbm_ncm_rel", "l10n_br_fiscal_nbm_l10n_br_fiscal_ncm_rel"),
    # l10n_br_fiscal/models/nbm.py: tax_definition_ids
    ("tax_definition_nbm_rel", "l10n_br_fiscal_nbm_l10n_br_fiscal_tax_definition_rel"),
    # l10n_br_fiscal/models/cest.py: ncm_ids
    ("fiscal_cest_ncm_rel", "l10n_br_fiscal_cest_l10n_br_fiscal_ncm_rel"),
    # l10n_br_fiscal/models/ncm.py: piscofins_ids
    (
        "fiscal_pis_cofins_ncm_rel",
        "l10n_br_fiscal_ncm_l10n_br_fiscal_tax_pis_cofins_rel",
    ),
    # l10n_br_fiscal/models/tax_definition.py: state_to_ids
    (
        "tax_definition_state_to_rel",
        "l10n_br_fiscal_tax_definition_res_country_state_rel",
    ),
    # l10n_br_fiscal/models/tax_definition.py: ncm_ids
    ("tax_definition_ncm_rel", "l10n_br_fiscal_ncm_l10n_br_fiscal_tax_definition_rel"),
    # l10n_br_fiscal/models/tax_definition.py: cest_ids
    (
        "tax_definition_cest_rel",
        "l10n_br_fiscal_cest_l10n_br_fiscal_tax_definition_rel",
    ),
    # l10n_br_fiscal/models/tax_definition.py: service_type_ids
    (
        "tax_definition_service_type_rel",
        "l10n_br_fiscal_service_type_l10n_br_fiscal_tax_definition_rel",
    ),
    # l10n_br_fiscal/models/simplified_tax.py: cnae_ids
    (
        "fiscal_simplified_tax_cnae_rel",
        "l10n_br_fiscal_cnae_l10n_br_fiscal_simplified_tax_rel",
    ),
]

_columns_renames = {
    # l10n_br_fiscal_operation_comment_rel
    # -> l10n_br_fiscal_comment_l10n_br_fiscal_operation_rel
    "l10n_br_fiscal_comment_l10n_br_fiscal_operation_rel": [
        ("fiscal_operation_id", "l10n_br_fiscal_operation_id"),
        ("comment_id", "l10n_br_fiscal_comment_id"),
    ],
    # l10n_br_fiscal_operation_line_comment_rel
    # -> l10n_br_fiscal_comment_l10n_br_fiscal_operation_line_rel
    "l10n_br_fiscal_comment_l10n_br_fiscal_operation_line_rel": [
        ("fiscal_operation_line_id", "l10n_br_fiscal_operation_line_id"),
        ("comment_id", "l10n_br_fiscal_comment_id"),
    ],
    # res_company_fiscal_cnae_rel -> l10n_br_fiscal_cnae_res_company_rel
    "l10n_br_fiscal_cnae_res_company_rel": [
        ("company_id", "res_company_id"),
        ("cnae_id", "l10n_br_fiscal_cnae_id"),
    ],
    # l10n_br_fiscal_document_mixin_comment_rel
    # -> l10n_br_fiscal_comment_l10n_br_fiscal_document_rel
    "l10n_br_fiscal_comment_l10n_br_fiscal_document_rel": [
        (
            "document_mixin_id",
            "l10n_br_fiscal_document_id",
        ),  # ORM uses concrete model table name
        ("comment_id", "l10n_br_fiscal_comment_id"),
    ],
    # fiscal_tax_rel -> l10n_br_fiscal_document_line_l10n_br_fiscal_tax_rel
    "l10n_br_fiscal_document_line_l10n_br_fiscal_tax_rel": [
        (
            "document_id",
            "l10n_br_fiscal_document_line_id",
        ),  # Old name was 'document_id', needs mapping to line
        ("fiscal_tax_id", "l10n_br_fiscal_tax_id"),
    ],
    # l10n_br_fiscal_document_line_mixin_comment_rel
    # -> l10n_br_fiscal_comment_l10n_br_fiscal_document_line_rel
    "l10n_br_fiscal_comment_l10n_br_fiscal_document_line_rel": [
        (
            "document_line_mixin_id",
            "l10n_br_fiscal_document_line_id",
        ),  # ORM uses concrete model table name
        ("comment_id", "l10n_br_fiscal_comment_id"),
    ],
    # fiscal_nbm_ncm_rel -> l10n_br_fiscal_nbm_l10n_br_fiscal_ncm_rel
    "l10n_br_fiscal_nbm_l10n_br_fiscal_ncm_rel": [
        ("nbm_id", "l10n_br_fiscal_nbm_id"),
        ("ncm_id", "l10n_br_fiscal_ncm_id"),
    ],
    # tax_definition_nbm_rel -> l10n_br_fiscal_nbm_l10n_br_fiscal_tax_definition_rel
    "l10n_br_fiscal_nbm_l10n_br_fiscal_tax_definition_rel": [
        ("nbm_id", "l10n_br_fiscal_nbm_id"),
        ("tax_definition_id", "l10n_br_fiscal_tax_definition_id"),
    ],
    # fiscal_cest_ncm_rel -> l10n_br_fiscal_cest_l10n_br_fiscal_ncm_rel
    "l10n_br_fiscal_cest_l10n_br_fiscal_ncm_rel": [
        ("cest_id", "l10n_br_fiscal_cest_id"),
        ("ncm_id", "l10n_br_fiscal_ncm_id"),
    ],
    # tax_definition_cest_rel -> l10n_br_fiscal_cest_l10n_br_fiscal_tax_definition_rel
    "l10n_br_fiscal_cest_l10n_br_fiscal_tax_definition_rel": [
        ("cest_id", "l10n_br_fiscal_cest_id"),
        ("tax_definition_id", "l10n_br_fiscal_tax_definition_id"),
    ],
    # fiscal_pis_cofins_ncm_rel -> l10n_br_fiscal_ncm_l10n_br_fiscal_tax_pis_cofins_rel
    "l10n_br_fiscal_ncm_l10n_br_fiscal_tax_pis_cofins_rel": [
        ("ncm_id", "l10n_br_fiscal_ncm_id"),
        ("piscofins_id", "l10n_br_fiscal_tax_pis_cofins_id"),
    ],
    # tax_definition_state_to_rel -> l10n_br_fiscal_tax_definition_res_country_state_rel
    "l10n_br_fiscal_tax_definition_res_country_state_rel": [
        ("tax_definition_id", "l10n_br_fiscal_tax_definition_id"),
        ("state_id", "res_country_state_id"),
    ],
    # tax_definition_ncm_rel -> l10n_br_fiscal_ncm_l10n_br_fiscal_tax_definition_rel
    "l10n_br_fiscal_ncm_l10n_br_fiscal_tax_definition_rel": [
        ("ncm_id", "l10n_br_fiscal_ncm_id"),
        ("tax_definition_id", "l10n_br_fiscal_tax_definition_id"),
    ],
    # tax_definition_service_type_rel
    # -> l10n_br_fiscal_service_type_l10n_br_fiscal_tax_definition_rel
    "l10n_br_fiscal_service_type_l10n_br_fiscal_tax_definition_rel": [
        ("tax_definition_id", "l10n_br_fiscal_tax_definition_id"),
        ("service_type_id", "l10n_br_fiscal_service_type_id"),
    ],
    # fiscal_simplified_tax_cnae_rel
    # -> l10n_br_fiscal_cnae_l10n_br_fiscal_simplified_tax_rel
    "l10n_br_fiscal_cnae_l10n_br_fiscal_simplified_tax_rel": [
        ("simplified_tax_id", "l10n_br_fiscal_simplified_tax_id"),
        ("cnae_id", "l10n_br_fiscal_cnae_id"),
    ],
    # custom table was preserved to avoid too long name
    # but column name change to default is still required:
    "tax_definition_city_taxation_code_rel": [
        ("tax_definition_id", "l10n_br_fiscal_tax_definition_id"),
        ("city_taxation_code_id", "l10n_br_fiscal_city_taxation_code_id"),
    ],
}


def rename_tables(cr, table_spec):
    """
    Rename tables without touching indexes or constraints.
    Verify that the table exists before renaming it.
    """
    for old, new in table_spec:
        # Check whether the table exists
        cr.execute("SELECT to_regclass(%s)", (old,))
        if cr.fetchone()[0] is None:
            _logger.info(f"Table {old} not found – skipping rename")
            continue

        _logger.info(f"Renaming table {old} → {new}")
        openupgrade.logged_query(
            cr,
            f"ALTER TABLE {old} RENAME TO {new}",
        )


def rename_columns(cr, column_spec):
    """
    Rename columns of existing tables.
    """
    for table, columns in column_spec.items():
        cr.execute("SELECT to_regclass(%s)", (table,))
        if cr.fetchone()[0] is None:
            _logger.info(f"Table {table} not found – skipping column renames")
            continue

        for old, new in columns:
            _logger.info(f"Renaming {table}.{old} → {new}")
            openupgrade.logged_query(
                cr,
                f"ALTER TABLE {table} RENAME {old} TO {new}",
            )


@openupgrade.migrate()
def migrate(env, version):
    """
    Migrate Many2many relation tables and columns from explicitly defined names
    to Odoo ORM defaults for l10n_br_fiscal module.
    """
    openupgrade.logged_query(
        env.cr, "DROP TABLE l10n_br_fiscal_tax_definition_res_country_state_rel;"
    )  # see https://github.com/OCA/l10n-brazil/issues/3748
    rename_tables(env.cr, _tables_renames)
    rename_columns(env.cr, _columns_renames)
