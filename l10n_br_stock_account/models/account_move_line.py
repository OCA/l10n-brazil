# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models
from odoo.tools import float_is_zero


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_stock_valuation_amount(self):
        """Valor que a fatura efetivamente debita na conta desta linha.

        É a soma do valor da própria linha com as linhas de imposto do
        lançamento que foram para a *mesma conta* da linha - tipicamente a
        conta ponte do estoque (``property_stock_account_input_categ_id``).

        As linhas de imposto do Odoo são agrupadas por imposto/conta, então uma
        mesma linha de imposto pode corresponder a várias linhas de produto.
        Por isso o valor é rateado pela participação desta linha na base do
        imposto.
        """
        self.ensure_one()
        amount = self.amount_currency
        tax_lines = self.move_id.line_ids.filtered(
            lambda line: line.tax_line_id and line.account_id == self.account_id
        )
        for tax_line in tax_lines:
            base_lines = self.move_id.invoice_line_ids.filtered(
                lambda line: tax_line.tax_line_id in line.tax_ids  # noqa: B023
            )
            base_amount = sum(base_lines.mapped("price_subtotal"))
            if self.currency_id.is_zero(base_amount):
                continue
            amount += tax_line.amount_currency * (self.price_subtotal / base_amount)
        return amount

    def _get_gross_unit_price(self):
        """Base unitária usada pelo core para valorar o estoque da entrada.

        O core devolve ``price_subtotal / quantity``. No Brasil essa base é
        bruta: o ICMS integra a própria base de cálculo (LC 87/96, art. 13,
        §1º, I) e o PIS/COFINS também vêm embutidos no preço. Mas os tributos
        recuperáveis não compõem o custo de aquisição - art. 301 do RIR/2018 e
        CPC 16, que exclui do custo dos estoques os tributos "recuperáveis
        junto ao fisco".

        Em vez de recalcular imposto aqui, usamos o que a própria fatura
        lançou: a base de valoração é o valor que a fatura debita na conta
        desta linha. Assim:

        * o resultado é o mesmo com ``deductible_taxes`` ligado ou desligado,
          porque nos dois casos o que sobra na conta ponte é o mesmo;
        * a creditabilidade sai da configuração do plano de contas, sem lista
          de CST nem regra em código - um imposto cuja linha de repartição não
          tem conta cai na conta da linha base e portanto *continua* no custo,
          que é a mesma convenção do core (ver ``total_void`` em
          ``account.tax.compute_all``).

        O nome do método é do core e fala de preço bruto; aqui ele devolve a
        base de valoração, que no Brasil é líquida. Renomear exigiria mexer no
        core, por isso a explicação fica neste docstring.
        """
        if not self.move_id.fiscal_operation_id:
            # Caso não tenha a Operação Fiscal não é um caso do Brasil
            return super()._get_gross_unit_price()

        if float_is_zero(
            self.quantity, precision_rounding=self.product_uom_id.rounding
        ):
            return super()._get_gross_unit_price()

        return self._get_stock_valuation_amount() / self.quantity
