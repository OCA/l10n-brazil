# Copyright 2023 Akretion (Raphaẽl Valyi <raphael.valyi@akretion.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DocumentImportWizard(models.TransientModel):
    """
    Extend the generic Document Importer so that importing
    a fiscal document will also create an account move and so
    it can be used sequencially with several attachments from
    the vendor bills upload button.
    """

    _inherit = "l10n_br_fiscal.document.import.wizard"

    # a transient wizard cannot be linked to any persistent
    # account.move record. So in case the user upload several
    # attachments, the solution we implemented
    # is to store the id of the 1st imported move and redirect
    # to the next imported account.move from there.
    first_imported_move_id = fields.Integer()

    def _check_imported_bill_allowed(self):
        """Refuse a vendor bill the inbox or an existing bill already blocks.

        Runs before the fiscal document is created, so a refused confirmation
        leaves no invoice behind.
        """
        self.ensure_one()
        if self.file and not (self.document_key or "").replace(" ", ""):
            self._onchange_file()
        key = (self.document_key or "").replace(" ", "")
        if not key:
            return
        inbox_model = self.env.get("l10n_br_fiscal_dfe.document")
        if inbox_model is not None and hasattr(inbox_model, "_check_import_allowed"):
            # The inbox import guard exists on later series only; 16.0 keeps
            # the check to the fiscal document already linked to bills below.
            inbox = inbox_model.search(
                [
                    ("access_key", "=", key),
                    ("company_id", "=", self.company_id.id),
                ],
                limit=1,
            )
            if inbox:
                inbox._check_import_allowed()
        document = self.env["l10n_br_fiscal.document"].search(
            [
                ("document_key", "=", key),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
        )
        if not document:
            return
        reason = document._vendor_bill_import_block_reason()
        if reason:
            raise UserError(reason)

    def action_import_and_open_move(self):
        """
        This is the import wizard confirmation action that will
        trigger the account.move importation for the current file.
        After the importation, it either redirect for processing
        the next file if any, either it redirect to the imported
        account.move(s) at the end of the attachments sequence.
        """
        self._check_imported_bill_allowed()
        _binding, fiscal_document = self._import_edoc()
        fiscal_document._check_document_import()
        move_type = f"{self.fiscal_operation_type}_invoice"
        # the bill belongs to the company of the document it comes from: its
        # journal (and hence its company and its taxes) is resolved there, not
        # in the user's current company
        move_model = self.env["account.move"].with_company(fiscal_document.company_id)
        # a bill may already exist for the order this document refers to: it
        # was converted from the purchase order to plan the outgoing cash flow
        # before the XML arrived, so rebuild it instead of duplicating it
        existing_move = self._find_draft_move_for_imported_document(
            fiscal_document, move_type
        )
        if existing_move:
            self._empty_draft_move_for_import(existing_move)
        move_id = move_model.import_fiscal_document(
            fiscal_document,
            move_id=existing_move.id,
            move_type=move_type,
            reset_header=bool(existing_move),
        ).id

        attachments = (
            self.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("res_model", "=", "l10n_br_fiscal.document.import.wizard"),
                    ("res_id", "=", self.id),
                    ("create_uid", "=", self._uid),
                ],
                order="id",
            )
        )
        if attachments:
            # then we should link the current attachment
            # to the imported account.move
            attachments[0].res_model = "account.move"
            attachments[0].res_id = move_id

        if len(attachments) > 1:
            # process the next files to import:
            return self._get_importer_action(attachments[1:], move_id=move_id)

        else:
            # no more file to import
            if not self.first_imported_move_id:
                # only one imported account move:
                return {
                    "name": _("Imported Invoice"),
                    "type": "ir.actions.act_window",
                    "target": "current",
                    "views": [[False, "form"]],
                    "res_id": move_id,
                    "res_model": "account.move",
                }
            else:  # several imported account moves:
                moves = self.env["account.move"].search(
                    [
                        ("imported_document", "=", True),
                        ("id", ">=", self.first_imported_move_id),
                        ("create_uid", "=", self._uid),
                    ]
                )
                return {
                    "name": _("Imported Invoices"),
                    "type": "ir.actions.act_window",
                    "target": "current",
                    "views": [[False, "tree"], [False, "form"]],
                    "res_ids": moves.ids,
                    "res_model": "account.move",
                }

    def _get_imported_order_references(self, fiscal_document):
        """Order references the imported document lines are tied to.

        ``partner_order`` is the xPed the supplier declared or, when it sent
        none, the reference synthesized from the match source the operator
        picked — the purchase order number in both cases. It is exactly what
        a bill converted from that order carries as ``invoice_origin``.
        """
        references = {
            (line.partner_order or "").strip()
            for line in fiscal_document.fiscal_line_ids
        }
        return sorted(reference for reference in references if reference)

    def _find_draft_move_for_imported_document(self, fiscal_document, move_type):
        """The draft bill already prepared for this document, if any.

        Converting a purchase order into a bill before the supplier XML
        arrives is a common way to plan the outgoing cash flow; importing the
        document afterwards must then re-use that bill instead of creating a
        twin. The lookup is generic on purpose — core ``account`` fields only,
        the order reference being what a bill converted from the order keeps
        in ``invoice_origin`` — so nothing here depends on purchase.

        Returns an empty recordset when there is nothing to re-use, and also
        when several drafts claim the same order: guessing which one is the
        right bill would be worse than importing into a new one.
        """
        references = self._get_imported_order_references(fiscal_document)
        if not references:
            return self.env["account.move"]
        moves = (
            self.env["account.move"]
            .with_company(fiscal_document.company_id)
            .search(
                [
                    ("move_type", "=", move_type),
                    ("state", "=", "draft"),
                    ("partner_id", "=", fiscal_document.partner_id.id),
                    ("company_id", "=", fiscal_document.company_id.id),
                    ("invoice_origin", "in", references),
                ]
            )
        )
        return moves if len(moves) == 1 else moves.browse()

    def _empty_draft_move_for_import(self, move):
        """Strip a draft bill of what was prepared from the order.

        Only the lines are recreated from the document: the bill itself — its
        journal, its dates, its payment terms, its link to the order — is
        kept, so the cash flow planning it was created for survives the
        import. The fiscal document lines delegated by those bill lines go
        with them, and the header is re-read from the imported document
        (``reset_header``).
        """
        move.ensure_one()
        move.invoice_line_ids.unlink()
        move.message_post(
            body=_(
                "Lines prepared from %(origin)s replaced by the lines of the "
                "imported fiscal document.",
                origin=move.invoice_origin,
            )
        )

    def _is_xml_attachment(self, attachment):
        if attachment.mimetype in ("application/xml", "text/xml"):
            return True
        return (attachment.name or "").lower().endswith(".xml")

    def _get_importer_action(self, attachments, move_id=None):
        """
        Try to parse the 1st XML of the attachments to
        detect its type and return the wizard import action.
        Also mark the other XML attachments to be imported next.
        """
        xml_attachments = attachments.filtered(self._is_xml_attachment)
        if not xml_attachments:
            raise UserError(
                _(
                    "None of the uploaded files is an XML: %(names)s",
                    names=", ".join(attachments.mapped("name")),
                )
            )
        ignored_attachments = attachments - xml_attachments
        if ignored_attachments:
            _logger.info(
                "Not importing the files that are not XML: %s",
                ", ".join(ignored_attachments.mapped("name")),
            )

        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "file": xml_attachments[0].datas,
                "file_name": xml_attachments[0].name,
                "first_imported_move_id": self.first_imported_move_id or move_id,
            }
        )

        for attachment in xml_attachments:
            # this link will allow to retrieve the next attachments to import:
            attachment.res_model = "l10n_br_fiscal.document.import.wizard"
            attachment.res_id = wizard.id

        wizard._onchange_file()
        return {
            "name": _("Adjust Importation"),
            "type": "ir.actions.act_window",
            "target": "new",
            "views": [[False, "form"]],
            "res_id": wizard.id,
            "res_model": "l10n_br_fiscal.document.import.wizard",
        }
