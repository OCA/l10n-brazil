# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=consider-merging-classes-inherited

from odoo import api, fields, models


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    import_state = fields.Selection(
        selection=[
            ("pending", "Pending Review"),
            ("in_progress", "Review in Progress"),
            ("resolved", "Resolved"),
        ],
        compute="_compute_import_state",
        store=True,
        copy=False,
        help="Review state of the lines of a document imported from a fiscal file.",
    )

    import_pending_count = fields.Integer(
        compute="_compute_import_pending_count",
    )

    @api.depends("imported_document", "fiscal_line_ids.import_state")
    def _compute_import_state(self):
        for document in self:
            if not document.imported_document:
                document.import_state = False
                continue
            states = set(document.fiscal_line_ids.mapped("import_state")) - {False}
            if not states or states == {"resolved"}:
                document.import_state = "resolved"
            elif "resolved" in states:
                document.import_state = "in_progress"
            else:
                document.import_state = "pending"

    @api.depends("fiscal_line_ids.import_state")
    def _compute_import_pending_count(self):
        for document in self:
            document.import_pending_count = len(
                document.fiscal_line_ids.filtered(
                    lambda line: line.import_state in ("pending", "matched")
                )
            )

    def _init_import_states(self):
        """Start the review of the lines of an imported document.

        A line with a product and a unit that is confirmed waits as a suggestion
        (``matched``); any other waits for a person (``pending``). A line that
        already has a state is a decision of a person and is left alone.
        """
        for line in self.filtered("imported_document").fiscal_line_ids:
            if not line.import_uom_factor:
                line.import_uom_factor = 1.0
            if line.import_state:
                continue
            matched = line.product_id and not line._import_unit_unconfirmed()
            line.import_state = "matched" if matched else "pending"

    def _suggest_fiscal_operation(self):
        """The operation most suggested among the lines, through the CFOP of the
        issuer."""
        self.ensure_one()
        suggestions = [
            operation
            for operation in (
                line._suggest_fiscal_operation_in() for line in self.fiscal_line_ids
            )
            if operation
        ]
        if not suggestions:
            return self.env["l10n_br_fiscal.operation"]
        return max(set(suggestions), key=suggestions.count)
