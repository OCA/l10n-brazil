# Copyright 2023 Akretion (Raphaẽl Valyi <raphael.valyi@akretion.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models
from odoo.exceptions import UserError


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
        if inbox_model is not None:
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
        move_id = (
            self.env["account.move"]
            .import_fiscal_document(
                fiscal_document,
                move_type=move_type,
            )
            .id
        )

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
                    "name": self.env._("Imported Invoice"),
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
                    "name": self.env._("Imported Invoices"),
                    "type": "ir.actions.act_window",
                    "target": "current",
                    "views": [[False, "tree"], [False, "form"]],
                    "res_ids": moves.ids,
                    "res_model": "account.move",
                }

    def _get_importer_action(self, attachments, move_id=None):
        """
        Try to parse the 1st file of the the attachments to
        detect its type and return the wizard import action.
        Also mark the other attachments to be imported next.
        """
        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "file": attachments[0].datas,
                "file_name": attachments[0].name,
                "first_imported_move_id": self.first_imported_move_id or move_id,
            }
        )

        for attachment in attachments:
            # this link will allow to retrieve the next attachments to import:
            attachment.res_model = "l10n_br_fiscal.document.import.wizard"
            attachment.res_id = wizard.id

        wizard._onchange_file()
        return {
            "name": self.env._("Adjust Importation"),
            "type": "ir.actions.act_window",
            "target": "new",
            "views": [[False, "form"]],
            "res_id": wizard.id,
            "res_model": "l10n_br_fiscal.document.import.wizard",
        }
