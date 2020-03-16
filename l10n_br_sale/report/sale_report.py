# Copyright (C) 2011  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"
    operation_id = fields.Many2one(
        "l10n_br_fiscal.operation", "Operation", readonly=True
    )

    def _select(self):
        return (
            super(SaleReport, self)._select()
            + ", l.operation_id as operation_id, "
        )

    def _group_by(self):
        return (
            super(SaleReport, self)._group_by()
            + ", l.operation_id"
        )
