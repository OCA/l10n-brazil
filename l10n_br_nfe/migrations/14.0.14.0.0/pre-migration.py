# Copyright 2024 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_field_renames = [
    (
        "l10n_br_fiscal.document.line",
        "l10n_br_fiscal_document_line",
        "nfe40_choice3",
        "nfe40_choice_tipi",
    ),
    (
        "l10n_br_fiscal.document.line",
        "l10n_br_fiscal_document_line",
        "nfe40_choice10",
        "nfe40_choice_imposto",
    ),
    (
        "l10n_br_fiscal.document.line",
        "l10n_br_fiscal_document_line",
        "nfe40_choice13",
        "nfe40_choice_pisoutr",
    ),
    (
        "l10n_br_fiscal.document.line",
        "l10n_br_fiscal_document_line",
        "nfe40_choice16",
        "nfe40_choice_cofinsoutr",
    ),
    (
        "l10n_br_fiscal.document.line",
        "l10n_br_fiscal_document_line",
        "nfe40_choice20",
        "nfe40_choice_ipitrib",
    ),
]


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if openupgrade.column_exists(
        env.cr, "l10n_br_fiscal_document_line", "nfe40_choice3"
    ):
        openupgrade.rename_fields(env, _field_renames)
