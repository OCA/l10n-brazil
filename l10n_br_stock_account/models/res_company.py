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
        default=True,
        help="Determina se o valor utilizado no custeamento automático será padrão do"
        " Odoo ou com base no campo stock_price_br.\n\n"
        "    * Usar True para valor de estoque líquido (sem imposto)",
    )
