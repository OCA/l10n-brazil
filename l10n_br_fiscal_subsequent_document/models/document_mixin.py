# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document_mixin"

    # FIXME the following onchange was extracted from
    # l10n_br_fiscal/models/document.py before
    # https://github.com/OCA/l10n-brazil/pull/3851
    #
    # @api.onchange("fiscal_operation_id")
    # def _onchange_fiscal_operation_id(self):
    #     result = super()._onchange_fiscal_operation_id()
    #     if self.fiscal_operation_id:
    #         self.fiscal_operation_type = (
    #             self.fiscal_operation_id.fiscal_operation_type
    #         )
    #         self.edoc_purpose = self.fiscal_operation_id.edoc_purpose
    #
    #     if self.issuer == DOCUMENT_ISSUER_COMPANY and not self.document_type_id:
    #         self.document_type_id = self.company_id.document_type_id
    #
    #     subsequent_documents = [Command.set({})]
    #     for subsequent_id in self.fiscal_operation_id.mapped(
    #         "operation_subsequent_ids"
    #     ):
    #         subsequent_documents.append(
    #             (
    #                 0,
    #                 0,
    #                 {
    #                     "source_document_id": self.id,
    #                     "subsequent_operation_id": subsequent_id.id,
    #                     "fiscal_operation_id": (
    #                         subsequent_id.subsequent_operation_id.id
    #                     ),
    #                 },
    #             )
    #         )
    #     self.document_subsequent_ids = subsequent_documents
    #     return result
