# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_PARTNER,
    DOCUMENT_STATE_DRAFT,
)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    import_document_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.document",
        compute="_compute_import_documents",
        string="Fiscal Documents",
        groups="l10n_br_fiscal.group_user",
        help="Technical: the imported fiscal documents whose lines point to a "
        "line of this order.",
    )
    import_document_count = fields.Integer(
        compute="_compute_import_documents",
        string="Fiscal docs",
        groups="l10n_br_fiscal.group_user",
    )

    @api.depends("order_line")
    def _compute_import_documents(self):
        # one reading for all the orders of the list
        lines = (
            self.env["l10n_br_fiscal.document.line"]
            .sudo()
            .search(
                [
                    ("import_purchase_line_id.order_id", "in", self.ids),
                    ("document_id.imported_document", "=", True),
                ]
            )
        )
        documents = {}
        for line in lines:
            order = line.import_purchase_line_id.order_id
            documents[order.id] = documents.get(order.id, line.document_id) | (
                line.document_id
            )
        for order in self:
            found = documents.get(order.id, self.env["l10n_br_fiscal.document"])
            order.import_document_ids = found
            order.import_document_count = len(found)

    def action_view_import_documents(self):
        """The imported fiscal document of the order, or the list of them."""
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

    def button_approve(self, force=False):
        result = super().button_approve(force=force)
        self._suggest_origin_on_imported_lines()
        return result

    def _suggest_origin_on_imported_lines(self):
        """A confirmed order becomes a candidate for the lines of the imported
        documents of its supplier that were waiting for it (a quotation, or an
        order created from the document itself)."""
        orders = self.filtered(lambda order: order.state in ("purchase", "done"))
        if not orders:
            return
        self.env["l10n_br_fiscal.document.line"].sudo().search(
            [
                ("document_id.imported_document", "=", True),
                ("document_id.state_edoc", "=", DOCUMENT_STATE_DRAFT),
                ("document_id.issuer", "=", DOCUMENT_ISSUER_PARTNER),
                ("document_id.fiscal_operation_type", "in", ("in", False)),
                ("document_id.company_id", "in", orders.company_id.ids),
                (
                    "document_id.partner_id.commercial_partner_id",
                    "in",
                    orders.partner_id.commercial_partner_id.ids,
                ),
                ("product_id", "in", orders.order_line.product_id.ids),
                ("import_purchase_line_id", "=", False),
            ]
        )._suggest_import_origin()
