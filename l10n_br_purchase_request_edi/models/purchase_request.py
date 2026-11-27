# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    import_document_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.document",
        compute="_compute_import_documents",
        string="Fiscal Documents",
        groups="l10n_br_fiscal.group_user",
        help="Technical: the imported fiscal documents whose lines point to a "
        "line of this request, or to an order line that was bought for it.",
    )
    import_document_count = fields.Integer(
        compute="_compute_import_documents",
        string="Fiscal docs",
        groups="l10n_br_fiscal.group_user",
    )

    @api.depends("line_ids")
    def _compute_import_documents(self):
        # one reading for all the requests of the list
        lines = (
            self.env["l10n_br_fiscal.document.line"]
            .sudo()
            .search(
                [
                    ("document_id.imported_document", "=", True),
                    "|",
                    ("import_request_line_id.request_id", "in", self.ids),
                    (
                        "import_purchase_line_id.purchase_request_lines.request_id",
                        "in",
                        self.ids,
                    ),
                ]
            )
        )
        documents = {}
        for line in lines:
            requests = (
                line.import_request_line_id.request_id
                | line.import_purchase_line_id.purchase_request_lines.request_id
            )
            for request in requests:
                documents[request.id] = documents.get(request.id, line.document_id) | (
                    line.document_id
                )
        for request in self:
            found = documents.get(request.id, self.env["l10n_br_fiscal.document"])
            request.import_document_ids = found
            request.import_document_count = len(found)

    def action_view_import_documents(self):
        """The imported fiscal document of the request, or the list of them."""
        self.ensure_one()
        documents = self.sudo().import_document_ids
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_br_fiscal_edi.imported_document_action"
        )
        if len(documents) == 1:
            action["views"] = [(False, "form")]
            action["res_id"] = documents.id
        else:
            action["domain"] = [("id", "in", documents.ids)]
        return action
