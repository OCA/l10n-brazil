# Copyright 2021 - TODAY, Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FiscalLineMixin(models.AbstractModel):
    _name = "l10n_br_repair.fiscal.line.mixin"
    _inherit = ["l10n_br_fiscal.document.line.mixin"]
    _description = "Fiscal Line Mixin"

    @api.model
    def _default_fiscal_operation(self):
        return self.env.company.repair_fiscal_operation_id

    @api.model
    def _fiscal_operation_domain(self):
        return [("state", "=", "approved")]

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    price_subtotal = fields.Monetary(
        related="fiscal_amount_untaxed",
        string="Subtotal",
    )

    price_total = fields.Monetary(
        related="fiscal_amount_total",
    )
