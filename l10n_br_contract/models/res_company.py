# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    contract_sale_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Default Contract Sale Fiscal Operation",
        required=False,
    )

    contract_purchase_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Default Contract Purchase Fiscal Operation",
        required=False,
    )

    contract_recalculate_taxes_before_invoice = fields.Boolean(
        string="Dafault recalculate taxes before invoicing", default=True
    )
