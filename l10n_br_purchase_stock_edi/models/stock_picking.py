# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    show_propose_lots_from_import = fields.Boolean(
        compute="_compute_show_propose_lots_from_import",
        help="Technical: a receipt waiting for lots whose moves are the origin "
        "of imported document lines that declare lots.",
    )

    @api.depends("state", "move_ids")
    def _compute_show_propose_lots_from_import(self):
        for picking in self:
            picking.show_propose_lots_from_import = bool(
                picking.state not in ("done", "cancel")
                and any(move._import_declared_lots() for move in picking.move_ids)
            )

    import_document_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.document",
        compute="_compute_import_documents",
        string="Fiscal Documents",
        groups="l10n_br_fiscal.group_user",
        help="Technical: the imported fiscal documents whose lines point to a "
        "move of this receipt.",
    )
    import_document_count = fields.Integer(
        compute="_compute_import_documents",
        string="Fiscal docs",
        groups="l10n_br_fiscal.group_user",
    )

    @api.depends("move_ids")
    def _compute_import_documents(self):
        # one reading for all the receipts of the list
        lines = (
            self.env["l10n_br_fiscal.document.line"]
            .sudo()
            .search(
                [
                    ("import_stock_move_id.picking_id", "in", self.ids),
                    ("document_id.imported_document", "=", True),
                ]
            )
        )
        documents = {}
        for line in lines:
            picking = line.import_stock_move_id.picking_id
            documents[picking.id] = documents.get(picking.id, line.document_id) | (
                line.document_id
            )
        for picking in self:
            found = documents.get(picking.id, self.env["l10n_br_fiscal.document"])
            picking.import_document_ids = found
            picking.import_document_count = len(found)

    def action_view_import_documents(self):
        """The imported fiscal document of the receipt, or the list of them."""
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

    def action_propose_lots_from_import(self):
        """Propose, on the receipt, the lots and expiry dates the document that is
        the origin of its moves declared. The operator reviews and validates."""
        self.ensure_one()
        reasons = []
        proposed = 0
        for move in self.move_ids:
            if not move._import_declared_lots():
                continue
            reason = move._propose_lots_from_import()
            if reason:
                reasons.append(reason)
            else:
                proposed += 1
        message = _("%s move(s) received the lots of the document.", proposed)
        if reasons:
            message += "\n" + "\n".join(reasons)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Lots of the document"),
                "message": message,
                "type": "success" if proposed else "warning",
                "sticky": bool(reasons),
            },
        }
