# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DocumentImportWizard(models.TransientModel):
    _inherit = "l10n_br_fiscal_edi.document.import.wizard"

    access_key = fields.Char(
        help="Access key of a note issued to a company of the user: the note is "
        "taken from the DF-e inbox or asked from the distribution service.",
    )

    state = fields.Selection(
        selection=[("draft", "Draft"), ("confirm", "Confirm")],
        default="draft",
    )

    confirm_message = fields.Text(readonly=True)

    dfe_document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal_dfe.document",
        readonly=True,
    )

    def action_import(self):
        self.ensure_one()
        access_key = self.env["dfe.specific.search.wizard"]._sanitize_access_key(
            self.access_key
        )
        if access_key and self.attachment_ids:
            raise UserError(_("Inform the access key or upload files, not both."))
        if access_key:
            return self._import_access_key(access_key)
        if self.dfe_document_id:
            return self._import_dfe_document(self.dfe_document_id)
        if not self.attachment_ids:
            raise UserError(_("Inform the access key or upload at least one file."))
        return super().action_import()

    def action_confirm_request(self):
        self.ensure_one()
        self.dfe_document_id._dfe_import_request()
        return self._notification(
            _("Import requested"),
            _(
                "The fiscal document will be created when the complete XML "
                "arrives from the distribution service."
            ),
            "info",
            {"type": "ir.actions.act_window_close"},
        )

    def _import_access_key(self, access_key):
        self.env["dfe.specific.search.wizard"]._validate_access_key(access_key)
        fiscal_type = self.env["l10n_br_fiscal_dfe.document"]._dfe_fiscal_type_from_key(
            access_key
        )
        # Before any query to the outside: a note that was already imported
        existing = self.env["l10n_br_fiscal.document"].search(
            [
                ("document_key", "=", access_key),
                ("company_id", "in", self.env.companies.ids),
            ],
            limit=1,
        )
        if existing:
            return self._notification(
                _("Note already imported"),
                _("This note was already imported; the existing document was opened."),
                "info",
                self._documents_action(existing),
            )
        dfe_document = self._find_dfe_document(access_key)
        if not dfe_document:
            self._search_distribution(fiscal_type, access_key)
            dfe_document = self._find_dfe_document(access_key)
        if not dfe_document:
            raise UserError(
                _(
                    "The note was not found in the distribution service. Upload "
                    "its XML file instead."
                )
            )
        self.dfe_document_id = dfe_document
        return self._import_dfe_document(dfe_document)

    def _find_dfe_document(self, access_key):
        return (
            self.env["l10n_br_fiscal_dfe.document"]
            .sudo()
            .search(
                [
                    ("access_key", "=", access_key),
                    ("company_id", "=", self.env.company.id),
                ],
                limit=1,
            )
        )

    def _search_distribution(self, fiscal_type, access_key):
        # The inbox is read-only for the fiscal user: the query writes the log
        # and the records of the distribution, which sudo keeps as the user's
        try:
            self.env.company.sudo()._dfe_search_specific_document(
                fiscal_type, access_key=access_key
            )
        except UserError:
            raise
        except Exception as error:  # pylint: disable=broad-except
            _logger.warning("DF-e query of %s failed", access_key, exc_info=True)
            raise UserError(
                _(
                    "The distribution service could not be reached now. Try "
                    "again later or upload the XML file of the note."
                )
            ) from error

    def _import_dfe_document(self, dfe_document):
        reason = dfe_document._dfe_import_block_reason()
        if reason:
            raise UserError(reason)
        complete = dfe_document._get_complete_dfe()
        if complete.attachment_id:
            attachment = complete.attachment_id.with_context(bin_size=False)
            return self._import_files(
                [(attachment.name, attachment.raw)], dfe_document=dfe_document
            )
        message = dfe_document._dfe_import_confirmation_message()
        if not message:
            dfe_document._dfe_import_request()
            return self._notification(
                _("Waiting for the XML"),
                _(
                    "The request is registered. The fiscal document will be "
                    "created when the complete XML arrives."
                ),
                "info",
                {"type": "ir.actions.act_window_close"},
            )
        self.write(
            {
                "state": "confirm",
                "dfe_document_id": dfe_document.id,
                "confirm_message": message,
            }
        )
        return {
            "name": _("Import Fiscal Document"),
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "views": [(False, "form")],
            "view_mode": "form",
            "target": "new",
        }
