# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

REQUEST_GROUP = "purchase_request.group_purchase_request_user"


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    import_request_ids = fields.Many2many(
        comodel_name="purchase.request",
        compute="_compute_import_requests",
        string="Purchase Requests",
        groups=REQUEST_GROUP,
        help="Technical: the purchase requests of the lines of the document: the "
        "one an order was created from and the ones of the order lines that the "
        "lines point to, as resolved or as suggested.",
    )
    import_request_count = fields.Integer(
        compute="_compute_import_requests",
        string="Requests",
        groups=REQUEST_GROUP,
    )

    def _import_requests(self):
        self.ensure_one()
        lines = self.sudo().fiscal_line_ids
        return (
            lines.import_request_line_id.request_id
            | lines.import_purchase_line_id.purchase_request_lines.request_id
        )

    @api.depends(
        "fiscal_line_ids.import_request_line_id",
        "fiscal_line_ids.import_purchase_line_id",
    )
    def _compute_import_requests(self):
        for document in self:
            requests = document._import_requests()
            document.import_request_ids = requests
            document.import_request_count = len(requests)

    def action_view_import_requests(self):
        """The purchase request of the document, or the list when there are
        several."""
        self.ensure_one()
        requests = self._import_requests()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "purchase_request.purchase_request_form_action"
        )
        if len(requests) == 1:
            action["views"] = [(False, "form")]
            action["res_id"] = requests.id
        else:
            action["domain"] = [("id", "in", requests.ids)]
        return action
