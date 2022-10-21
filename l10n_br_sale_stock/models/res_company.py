# Copyright (C) 2021 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_create_invoice_policy = fields.Selection(
        selection=[
            ("sale_order", _("Sale Order")),
            ("stock_picking", _("Stock Picking")),
        ],
        help="Define, when Product Type are not service, if Invoice"
        " should be create from Sale Order or Stock Picking.",
        default="stock_picking",
    )
