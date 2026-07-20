# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountTax(models.Model):
    _name = "account.tax"
    _inherit = ["account.tax.mixin", "account.tax"]

    def _setup_no_credit_repartition(self):
        """Par de repartições tax +100/-100 sem contas: a soma dos fatores é
        zero, então o compute_all brasileiro produz amount contábil 0 (nenhuma
        linha no razão) enquanto o valor do imposto por fora continua compondo
        o total da fatura. Usado pelas variantes "s/ Crédito"."""
        for tax in self:
            for rep_field in (
                "invoice_repartition_line_ids",
                "refund_repartition_line_ids",
            ):
                rep_tax = tax[rep_field].filtered(
                    lambda line: line.repartition_type == "tax"
                )
                if len(rep_tax) == 1:
                    rep_tax.account_id = False
                    rep_tax.factor_percent = 100
                    rep_tax.copy(
                        {
                            "factor_percent": -100,
                            "account_id": False,
                        }
                    )
                elif rep_tax:
                    rep_tax.write({"account_id": False})

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
            # Para dedutíveis/retidos o factor -100 precisa ser aplicado mesmo
            # quando a conta é vazia (crédito neteando a conta da linha do
            # produto — dedutíveis de compra).
            if refund_repartition_line and (
                refund_account_id or tax.deductible or tax.withholdable
            ):
                refund_repartition_line.account_id = refund_account_id
                refund_repartition_line.factor_percent = (
                    -100 if tax.deductible or tax.withholdable else 100
                )
