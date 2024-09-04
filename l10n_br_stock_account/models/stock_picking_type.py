# Copyright (C) 2011  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Default Fiscal Operation",
        domain="[('state', '=', 'approved')]",
    )

    pre_generate_fiscal_document_number = fields.Selection(
        selection=[
            ("none", "None"),
            ("pack", "Pack"),
            ("validate", "Validate"),
            ("invoice_wizard", "Invoice Create Wizard"),
        ],
        default="none",
        string="Pré generate Fiscal Document Number",
        help="Check this box if you want to generate fiscal document for this "
        "operation.",
    )
