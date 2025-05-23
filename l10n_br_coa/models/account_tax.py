# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountTax(models.Model):
    _name = "account.tax"
    _inherit = ["account.tax.mixin", "account.tax"]

    def _update_repartition_lines(self, account_id, refund_account_id):
        for tax in self:
            invoice_repartion_line = tax.invoice_repartition_line_ids.filtered(
                lambda line: line.repartition_type == "tax"
            )
            if invoice_repartion_line:
                invoice_repartion_line.account_id = account_id
                invoice_repartion_line.factor_percent = (
                    -100 if tax.deductible or tax.withholdable else 100
                )

            refund_repartition_line = tax.refund_repartition_line_ids.filtered(
                lambda line: line.repartition_type == "tax"
            )
            if refund_account_id:
                refund_repartition_line.account_id = refund_account_id
                refund_repartition_line.factor_percent = (
                    -100 if tax.deductible or tax.withholdable else 100
                )
