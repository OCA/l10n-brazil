# Copyright (C) 2021 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3.0 or later (
# http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_field_renames = [
    (
        "l10n_br_fiscal.document.related",
        "l10n_br_fiscal_document_related",
        "date",
        "document_date",
    ),
    ("l10n_br_fiscal.document", "l10n_br_fiscal_document", "date", "document_date"),
]


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.rename_fields(env, _field_renames)
