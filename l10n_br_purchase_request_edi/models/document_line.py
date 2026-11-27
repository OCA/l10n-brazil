# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    import_request_line_id = fields.Many2one(
        comodel_name="purchase.request.line",
        string="Purchase Request Line",
        copy=False,
        index=True,
        ondelete="set null",
        groups="purchase_request.group_purchase_request_user",
        help="Purchase request line the order of this imported document line "
        "was created from. While the order waits for its approval the origin "
        "is only suggested and it is resolved when the order is confirmed.",
    )

    def write(self, vals):
        result = super().write(vals)
        if "import_purchase_line_id" in vals and "import_request_line_id" not in vals:
            # the origin changed: it does not come from the request any longer.
            # Done with sudo because a user of the fiscal group changes the origin
            # and cannot write the field of the request.
            self.sudo().filtered("import_request_line_id").write(
                {"import_request_line_id": False}
            )
        return result

    def _suggest_import_origin(self):
        # an order created from a request and waiting for its approval is a
        # decision of the person, not a suggestion to be recomputed
        lines = self.filtered(lambda line: not line.sudo().import_request_line_id)
        return super(FiscalDocumentLine, lines)._suggest_import_origin()
