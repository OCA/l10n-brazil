# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    @api.model
    def _fiscal_operation_domain(self):
        return [
            ("fiscal_operation_type", "=", "out"),
            ("state", "=", "approved"),
            ("fiscal_type", "not ilike", "%refund%"),
        ]

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Fiscal Operation",
        compute="_compute_fiscal_operation_id",
        store=True,
        readonly=False,
        precompute=True,
        domain=lambda self: self._fiscal_operation_domain(),
        help="Fiscal operation of the quotation created from the repair order "
        "and of its lines for the repair parts.",
    )

    @api.depends("company_id", "sale_order_id.fiscal_operation_id")
    def _compute_fiscal_operation_id(self):
        for repair in self:
            if repair.sale_order_id:
                repair.fiscal_operation_id = repair.sale_order_id.fiscal_operation_id
            elif not repair.fiscal_operation_id:
                repair.fiscal_operation_id = (
                    repair.company_id.repair_fiscal_operation_id
                )
