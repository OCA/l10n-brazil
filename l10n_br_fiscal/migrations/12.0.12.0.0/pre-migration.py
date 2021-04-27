# Copyright (C) 2021 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3.0 or later (
# http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_model_renames = [
    ("l10n_br_fiscal.document.invalidate.number", "l10n_br_fiscal.invalidate.number"),
]

_table_renames = [
    ("l10n_br_fiscal_document_invalidate_number", "l10n_br_fiscal_invalidate_number"),
]

_column_renames = {
    "l10n_br_fiscal_document": [
        ("codigo_situacao", "status_code"),
        ("motivo_situacao", "status_name"),
        ("autorizacao_event_id", "authorization_event_id"),
        ("file_pdf_id", "file_report_id"),
        ("key", "document_key"),
    ],
    "l10n_br_fiscal_document_event": [
        ("fiscal_document_id", "document_id"),
        ("file_sent", "file_request_id"),
        ("file_returned", "file_response_id"),
        ("status", "status_code"),
        ("end_date", "protocol_date"),
    ],
    "l10n_br_fiscal_document_related": [
        ("fiscal_document_id", "document_id"),
    ],
}


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.rename_models(env.cr, _model_renames)
    openupgrade.rename_tables(env.cr, _table_renames)
    openupgrade.rename_columns(env.cr, _column_renames)
