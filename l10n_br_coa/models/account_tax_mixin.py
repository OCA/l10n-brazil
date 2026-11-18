# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountTaxMixin(models.AbstractModel):
    _name = "account.tax.mixin"
    _description = "Account Tax Mixin"

    deductible = fields.Boolean(
        string="Deductible Tax?",
        default=True,
    )

    withholdable = fields.Boolean(
        string="Withholdable Tax?",
        default=False,
    )

    @api.onchange("deductible", "withholdable")
    def _onchange_deductible(self):
        for repartition in self.invoice_repartition_line_ids.filtered(
            lambda r: r.repartition_type == "tax"
        ):
            repartition.factor_percent = (
                -100 if self.deductible or self.withholdable else 100
            )

        for repartition in self.refund_repartition_line_ids.filtered(
            lambda r: r.repartition_type == "tax"
        ):
            repartition.factor_percent = (
                -100 if self.deductible or self.withholdable else 100
            )
