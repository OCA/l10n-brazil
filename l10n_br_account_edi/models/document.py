# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_STATE_DRAFT,
)


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    edi_can_generate_invoice = fields.Boolean(
        compute="_compute_edi_can_generate_invoice",
        help="An imported document that was reviewed, has lines and an amount "
        "declared in the file, and has no invoice yet. It is not stored.",
    )

    @api.depends(
        "imported_document",
        "import_state",
        "move_ids",
        "fiscal_line_ids",
        "fiscal_operation_id",
        "fiscal_line_ids.fiscal_amount_total",
    )
    def _compute_edi_can_generate_invoice(self):
        for document in self:
            document.edi_can_generate_invoice = bool(
                document.imported_document
                and document.import_state == "resolved"
                and document.fiscal_line_ids
                and document._edi_payment_totals()[0]
                and not document.move_ids
                and not document._edi_no_payable_reason()
            )

    def action_generate_invoice(self):
        """Create the vendor bill of an imported document. The payables are born
        with it, not with the import."""
        self.ensure_one()
        # the invoice is born in the company of the document, whichever the user
        # has selected
        self = self.with_company(self.company_id)
        reason = self._edi_no_payable_reason()
        if reason:
            raise UserError(reason)
        if not self.env["account.move"].check_access_rights(
            "create", raise_exception=False
        ):
            raise UserError(
                _(
                    "Generating the invoice needs the accounting rights of the "
                    "Billing group. Ask a user that has them."
                )
            )
        if not self.fiscal_operation_id:
            raise UserError(
                _(
                    "The document has no fiscal operation. Choose it in the header "
                    "of the document before generating the invoice."
                )
            )
        if not self.partner_id:
            raise UserError(
                _(
                    "The document has no partner. Choose it before generating the "
                    "invoice."
                )
            )
        pending = self.fiscal_line_ids.filtered(
            lambda line: line.import_state != "resolved"
        )
        if pending:
            raise UserError(
                _("Resolve the lines before generating the invoice:\n%s")
                % "\n".join(f"- {line.name}" for line in pending)
            )
        self._check_document_import()
        try:
            move_form = self.env["account.move"].import_fiscal_document(
                self, move_type=f"{self.fiscal_operation_type}_invoice"
            )
        except AssertionError as error:
            # the form of the invoice refuses what it requires or hides
            raise UserError(
                _("The invoice could not be created from this document: %s") % error
            ) from error
        return {
            "name": _("Invoice"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": move_form.id,
            "views": [(False, "form")],
            "view_mode": "form",
            "target": "current",
        }

    def _edi_demo_post_invoice(self):
        """Demo data: the invoice of a reviewed imported document, generated and
        posted, to show the whole cycle of life of the import."""
        for document in self:
            action = document.action_generate_invoice()
            self.env["account.move"].browse(action["res_id"]).action_post()

    def _edi_draft_move(self):
        """The draft invoice that will issue this document, if there is one."""
        self.ensure_one()
        if not self.env["account.move"].check_access_rights(
            "read", raise_exception=False
        ):
            return self.env["account.move"]
        if (
            self.issuer == DOCUMENT_ISSUER_COMPANY
            and not self.imported_document
            and self.state_edoc == DOCUMENT_STATE_DRAFT
        ):
            return self.move_ids[:1]
        return self.env["account.move"]

    def _edi_display_installments(self):
        move = self._edi_draft_move()
        return move._edi_installments() if move else super()._edi_display_installments()

    def _edi_display_payments(self):
        move = self._edi_draft_move()
        return move._edi_payments() if move else super()._edi_display_payments()
