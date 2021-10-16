# Copyright (C) 2013  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from ..constants.fiscal import (
    CFOP_DESTINATION,
    CFOP_TYPE_MOVE,
    CFOP_TYPE_MOVE_DEFAULT,
    FISCAL_IN_OUT,
    FISCAL_OUT,
)


class Cfop(models.Model):
    _name = "l10n_br_fiscal.cfop"
    _inherit = "l10n_br_fiscal.data.abstract"
    _description = "CFOP"

    code = fields.Char(size=4)

    small_name = fields.Char(string="Small Name", size=32, required=True)

    type_in_out = fields.Selection(
        selection=FISCAL_IN_OUT, string="Type", required=True, default=FISCAL_OUT
    )

    destination = fields.Selection(
        selection=CFOP_DESTINATION,
        string="Destination",
        required=True,
        help="Identifies the operation destination.",
    )

    cfop_inverse_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="Inverse CFOP",
        domain="[('destination', '=', destination),"
        "('type_in_out', '!=', type_in_out)]",
    )

    cfop_return_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="Return CFOP",
        domain="[('destination', '=', destination),"
        "('type_in_out', '!=', type_in_out),"
        "('type_move', 'in', ('sale_refund',"
        " 'purchase_refund', 'return_out', 'return_in'))]",
    )

    stock_move = fields.Boolean(string="Stock Moves?", default=True)

    finance_move = fields.Boolean(string="Finance Moves?", default=True)

    account_move = fields.Boolean(string="Account Move?", default=True)

    assent_move = fields.Boolean(string="Assent Move?", default=False)

    type_move = fields.Selection(
        selection=CFOP_TYPE_MOVE,
        string="Type Move",
        required=True,
        default=CFOP_TYPE_MOVE_DEFAULT,
    )

    tax_definition_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.tax.definition",
        inverse_name="cfop_id",
        string="Tax Definition",
    )

    _sql_constraints = [
        (
            "fiscal_cfop_code_uniq",
            "unique (code)",
            "CFOP already exists with this code !",
        )
    ]
