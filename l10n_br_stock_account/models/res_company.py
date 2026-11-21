# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    stock_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        domain=[("state", "=", "approved")],
    )

    stock_in_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        domain=[("state", "=", "approved"), ("fiscal_operation_type", "=", "in")],
    )

    stock_out_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        domain=[("state", "=", "approved"), ("fiscal_operation_type", "=", "out")],
    )

    stock_valuation_via_stock_price = fields.Boolean(
        string="Valuation Via Stock Price",
        default=False,
        help="Whether stock is valued at the Odoo default price or at the net"
        " acquisition cost, that is, the invoice total minus the taxes this"
        " company can recover (art. 301 RIR/2018, CPC 16).\n\n"
        "    * True values incoming stock net of recoverable taxes.\n"
        "    Opt-in: the False default keeps existing databases unchanged.",
    )
