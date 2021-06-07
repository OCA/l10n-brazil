# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Fiscal Operation",
        readonly=True,
    )

    fiscal_operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Fiscal Operation Line",
        readonly=True,
    )

    def _select(self):
        select_str = super()._select()
        select_str += """
            , l.fiscal_operation_id as fiscal_operation_id,
            l.fiscal_operation_line_id as fiscal_operation_line_id
        """
        return select_str

    def _group_by(self):
        group_by_str = super()._group_by()
        group_by_str += """
            , l.fiscal_operation_id,
            l.fiscal_operation_line_id
        """
        return group_by_str
