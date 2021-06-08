# Copyright (C) 2021 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3.0 or later (
# http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_model_renames = [
    ("l10n_br_fiscal.document.invalidate.number", "l10n_br_fiscal.invalidate.number"),
    ("l10n_br_fiscal.document.event", "l10n_br_fiscal.event"),
]

_table_renames = [
    ("l10n_br_fiscal_document_invalidate_number", "l10n_br_fiscal_invalidate_number"),
    ("l10n_br_fiscal_document_event", "l10n_br_fiscal_event"),
]

_field_renames = [
    (
        "l10n_br_fiscal.document.related",
        "l10n_br_fiscal_document_related",
        "fiscal_document_id",
        "document_id",
    ),
    (
        "l10n_br_fiscal.document.related",
        "l10n_br_fiscal_document_related",
        "key",
        "document_key",
    ),
    (
        "l10n_br_fiscal.document.related",
        "l10n_br_fiscal_document_related",
        "number",
        "document_number",
    ),
    (
        "l10n_br_fiscal.document.related",
        "l10n_br_fiscal_document_related",
        "serie",
        "document_serie",
    ),
    (
        "l10n_br_fiscal.event",
        "l10n_br_fiscal_event",
        "fiscal_document_id",
        "document_id",
    ),
    ("l10n_br_fiscal.event", "l10n_br_fiscal_event", "file_sent", "file_request_id"),
    (
        "l10n_br_fiscal.event",
        "l10n_br_fiscal_event",
        "file_returned",
        "file_response_id",
    ),
    ("l10n_br_fiscal.event", "l10n_br_fiscal_event", "status", "status_code"),
    ("l10n_br_fiscal.event", "l10n_br_fiscal_event", "end_date", "protocol_date"),
    (
        "l10n_br_fiscal.document",
        "l10n_br_fiscal_document",
        "codigo_situacao",
        "status_code",
    ),
    (
        "l10n_br_fiscal.document",
        "l10n_br_fiscal_document",
        "motivo_situacao",
        "status_name",
    ),
    (
        "l10n_br_fiscal.document",
        "l10n_br_fiscal_document",
        "autorizacao_event_id",
        "authorization_event_id",
    ),
    (
        "l10n_br_fiscal.document",
        "l10n_br_fiscal_document",
        "file_pdf_id",
        "file_report_id",
    ),
    ("l10n_br_fiscal.document", "l10n_br_fiscal_document", "key", "document_key"),
    ("l10n_br_fiscal.document", "l10n_br_fiscal_document", "number", "document_number"),
]


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if openupgrade.table_exists(env.cr, "l10n_br_fiscal_document_invalidate_number"):
        openupgrade.rename_models(env.cr, _model_renames)
        openupgrade.rename_tables(env.cr, _table_renames)
        openupgrade.rename_fields(env, _field_renames)
