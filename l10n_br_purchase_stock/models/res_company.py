# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models


class Company(models.Model):
    _inherit = "res.company"

    purchase_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Default Fiscal Operation for Purchase",
        domain=[("state", "=", "approved"), ("fiscal_type", "=", "purchase")],
    )

    purchase_create_invoice_policy = fields.Selection(
        selection=[
            ("purchase_order", _("Purchase Order")),
            ("stock_picking", _("Stock Picking")),
        ],
        string="Purchase Create Invoice Policy",
        default="purchase_order",
    )
