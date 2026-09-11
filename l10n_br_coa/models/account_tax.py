# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountTax(models.Model):
    _name = "account.tax"
    _inherit = ["account.tax.mixin", "account.tax"]

    @api.model
    def _distribute_delta_amount_smoothly(
        self, precision_digits, delta_amount, target_factors
    ):
        # A withholding or deductible tax carries a single tax repartition line
        # with a negative factor, so the regular branch of
        # _add_accounting_data_to_base_line_tax_details, which keeps only
        # factors >= 0, hands over an empty list while the delta still holds the
        # whole tax amount. Distributing it then indexes an empty list. There is
        # no repartition line to carry the delta: the reverse charge branch is
        # the one that books these taxes.
        if not target_factors:
            return []
        return super()._distribute_delta_amount_smoothly(
            precision_digits, delta_amount, target_factors
        )

    def _update_repartition_lines(self, account_id, refund_account_id):
        for tax in self:
            # Ensure repartition lines are created (trigger computed fields)
            # In Odoo 18, these are computed fields that may not be triggered yet
            if not tax.invoice_repartition_line_ids:
                tax._compute_invoice_repartition_line_ids()
            if not tax.refund_repartition_line_ids:
                tax._compute_refund_repartition_line_ids()

            # Flush to ensure repartition lines are persisted before filtering
            tax.flush_recordset(
                ["invoice_repartition_line_ids", "refund_repartition_line_ids"]
            )

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
            if refund_repartition_line and refund_account_id:
                refund_repartition_line.account_id = refund_account_id
                refund_repartition_line.factor_percent = (
                    -100 if tax.deductible or tax.withholdable else 100
                )
