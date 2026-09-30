# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountTax(models.Model):
    _name = "account.tax"
    _inherit = ["account.tax.mixin", "account.tax"]

    def _update_repartition_lines(self, account_id, refund_account_id):
        for tax in self:
            # Ensure repartition lines are created (trigger computed fields)
            if not tax.repartition_line_ids:
                tax._compute_invoice_repartition_line_ids()
                tax._compute_refund_repartition_line_ids()

            # Flush to ensure repartition lines are persisted before filtering
            tax.flush_recordset(["repartition_line_ids"])

            factor_percent = -100 if tax.deductible or tax.withholdable else 100
            for repartition_line in tax.repartition_line_ids.filtered(
                lambda line: line.repartition_type == "tax"
            ):
                if repartition_line.document_type == "refund":
                    if not refund_account_id:
                        continue
                    repartition_line.account_id = refund_account_id
                else:
                    repartition_line.account_id = account_id
                repartition_line.factor_percent = factor_percent
