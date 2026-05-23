# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_AUTORIZADA,
)


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    document_subsequent_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.subsequent.document",
        inverse_name="source_document_id",
        copy=True,
    )

    document_subsequent_generated = fields.Boolean(
        string="Subsequent documents generated?",
        compute="_compute_document_subsequent_generated",
        default=False,
    )

    def _prepare_referenced_subsequent(self, doc_referenced):
        self.ensure_one()
        return {
            "document_id": self.id,
            "document_related_id": doc_referenced.id,
            "document_type_id": doc_referenced.document_type_id.id,
            "document_serie": doc_referenced.document_serie,
            "document_number": doc_referenced.document_number,
            "document_date": doc_referenced.document_date,
            "document_key": doc_referenced.document_key,
        }

    def _document_reference(self, documents_referenced):
        self.ensure_one()
        for doc_referenced in documents_referenced:
            self.env["l10n_br_fiscal.document.related"].create(
                self._prepare_referenced_subsequent(doc_referenced)
            )

    @api.depends("document_subsequent_ids.subsequent_document_id")
    def _compute_document_subsequent_generated(self):
        for document in self:
            if not document.document_subsequent_ids:
                document.document_subsequent_generated = False
            else:
                document.document_subsequent_generated = all(
                    subsequent_id.operation_performed
                    for subsequent_id in document.document_subsequent_ids
                )

    def _generates_subsequent_operations(self):
        for record in self.filtered(lambda doc: not doc.document_subsequent_generated):
            for subsequent_id in record.document_subsequent_ids.filtered(
                lambda doc_sub: doc_sub._confirms_document_generation()
            ):
                subsequent_id.generate_subsequent_document()

    def cancel_edoc(self):
        self.ensure_one()
        if any(
            doc.state_edoc == SITUACAO_EDOC_AUTORIZADA
            for doc in self.document_subsequent_ids.mapped("document_subsequent_ids")
        ):
            message = _(
                "Canceling the document is not allowed: one or more "
                "associated documents have already been authorized."
            )
            raise UserWarning(message)

    def _after_change_state(self, old_state, new_state):
        self.ensure_one()
        result = super()._after_change_state(old_state, new_state)
        self._generates_subsequent_operations()
        return result
