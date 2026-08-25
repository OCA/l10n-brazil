# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountTax(models.Model):
    _name = "account.tax"
    _inherit = ["account.tax.mixin", "account.tax"]

    def _update_repartition_lines(self, account_id, refund_account_id):
        for tax in self:
            factor_percent = -100 if tax.deductible or tax.withholdable else 100

            invoice_repartion_line = tax.invoice_repartition_line_ids.filtered(
                lambda line: line.repartition_type == "tax"
            )
            if invoice_repartion_line:
                invoice_repartion_line.account_id = account_id
                invoice_repartion_line.factor_percent = factor_percent

            refund_repartition_line = tax.refund_repartition_line_ids.filtered(
                lambda line: line.repartition_type == "tax"
            )
            if refund_repartition_line:
                # O fator precisa ser aplicado mesmo quando não há conta:
                # o imposto sem conta cai na conta da linha base, mas o sinal
                # continua vindo da natureza do imposto.
                refund_repartition_line.account_id = refund_account_id
                refund_repartition_line.factor_percent = factor_percent
