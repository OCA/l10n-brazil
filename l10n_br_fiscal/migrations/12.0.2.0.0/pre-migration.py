# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_column_renames = {
    'l10n_br_fiscal_operation_line': [
        ('operation_id', 'fiscal_operation_id')],
    'l10n_br_fiscal_tax_definition': [
        ('operation_line_id', 'fiscal_operation_line_id')],
    'l10n_br_fiscal_operation_document_type': [
        ('operation_id', 'fiscal_operation_id')],
    'l10n_br_fiscal_operation_comment_rel': [
        ('operation_id', 'fiscal_operation_id')],
    'l10n_br_fiscal_operation_line_comment_rel': [
        ('operation_id', 'fiscal_operation_line_id')],
    'l10n_br_fiscal_document': [
        ('operation_id', 'fiscal_operation_line_id')],
    'l10n_br_fiscal_document_line': [
        ('operation_id', 'fiscal_operation_line_id')],
    'l10n_br_fiscal_document_line': [
        ('operation_line_id', 'fiscal_operation_line_id')],
}


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.rename_columns(env.cr, _column_renames)
