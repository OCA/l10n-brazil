# Copyright 2026 - TODAY Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DocumentImportMatchLine(models.TransientModel):
    """One XML line the user can pair with an existing vendor bill line."""

    _name = "l10n_br_account.document.import.match.line"
    _description = "Imported fiscal line matched to a vendor bill line"
    _order = "sequence, id"

    wizard_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.import.wizard",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer()
    name = fields.Char()
    product_id = fields.Many2one(comodel_name="product.product")
    quantity = fields.Float()
    price_unit = fields.Float()
    partner_order = fields.Char()
    partner_order_line = fields.Char()
    invoice_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Vendor Bill Line",
        domain="["
        "('move_id', '=', parent.target_move_id), "
        "('display_type', '=', 'product')"
        "]",
    )
    ambiguous = fields.Boolean(
        help="More than one vendor bill line could receive this XML line.",
    )
