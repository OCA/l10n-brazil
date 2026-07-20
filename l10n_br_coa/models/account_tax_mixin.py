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

    no_credit = fields.Boolean(
        string="No Credit Variant?",
        default=False,
        help="Variante contábil para imposto POR FORA (ex.: IPI) numa compra"
        " SEM direito a crédito: o valor compõe o total da fatura (o"
        " fornecedor cobra), mas não gera lançamento contábil próprio — fica"
        " no custo da linha do produto. Tecnicamente: par de repartições"
        " +100/-100 sem contas (soma dos fatores 0 → amount contábil 0)."
        " Selecionada pelo resolvedor de creditabilidade"
        " (_get_stock_cost_tax_map) quando o imposto não credita.",
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
