# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import models
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_creditable_tax_value(self):
        """Soma dos impostos da linha que o plano de contas manda creditar.

        A creditabilidade não é decidida aqui: ela vem da existência de conta
        na linha de repartição do imposto contábil. `ICMS Entrada` aponta para
        `1.1.4.1.02 ICMS a Compensar`, logo o imposto foi creditado e sai do
        custo; `ICMS SN Entrada` e `ICMS Entrada Subist` não têm conta, caem na
        conta da linha base e continuam no custo. É a mesma convenção do
        `total_void` do core: imposto sem conta é custo.

        Só os impostos não dedutíveis são percorridos - são eles que carregam
        a conta do crédito. Os dedutíveis são a contrapartida, que sai da
        própria conta da linha.
        """
        self.ensure_one()
        total = 0.0
        for tax in self.tax_ids.filtered(lambda t: not t.deductible):
            repartition_line = tax.invoice_repartition_line_ids.filtered(
                lambda line: line.repartition_type == "tax"
            )
            if not repartition_line.account_id:
                # Sem conta o imposto cai na conta da linha base: é custo
                continue
            tax_domain = tax.tax_group_id.fiscal_tax_group_id.tax_domain
            if not tax_domain:
                continue
            total += getattr(self, f"{tax_domain}_value", 0.0) or 0.0
        return total

    def _get_net_cost_price_unit(self):
        """Custo líquido unitário da entrada.

        Parte do preço da linha e chega no valor que a fatura vai debitar na
        conta do estoque:

            líquido = bruto + impostos por fora - impostos creditados

        Os impostos "por fora" (IPI, ICMS ST) não estão no preço e precisam
        entrar no custo; se forem creditáveis, saem de novo no segundo termo.
        Ver `_get_stock_valuation_amount` no `l10n_br_stock_account`, que é o
        lado da fatura da mesma conta.
        """
        self.ensure_one()
        quantity = self.product_uom_qty
        if float_is_zero(quantity, precision_rounding=self.product_uom.rounding):
            return 0.0
        adjustment = self.amount_tax_not_included - self._get_creditable_tax_value()
        return self.price_unit + (adjustment / quantity)

    def _net_cost_applies(self):
        """Diz se a entrada pode ser valorizada pelo custo líquido."""
        self.ensure_one()
        if not self.fiscal_operation_line_id:
            # Sem linha de operação fiscal não há como saber o tratamento do
            # imposto: o custo líquido fica por conta da fatura
            return False
        if not self._is_in():
            return False
        return True

    def _action_done(self, cancel_backorder=False):
        # A valoração roda dentro do _action_done, então os campos fiscais
        # precisam estar atualizados antes. Em fluxo programático eles podem
        # estar defasados, e depois de "done" o recompute é bloqueado.
        self.filtered(lambda move: move._net_cost_applies())._compute_tax_fields()
        return super()._action_done(cancel_backorder=cancel_backorder)

    def _get_price_unit(self):
        result = super()._get_price_unit()
        if not self._net_cost_applies():
            return result

        creditable_tax_value = self._get_creditable_tax_value()
        if float_is_zero(
            creditable_tax_value,
            precision_rounding=self.company_id.currency_id.rounding,
        ):
            # Nada a creditar: o custo já é o bruto
            return result

        net_price_unit = self._get_net_cost_price_unit()
        if net_price_unit <= 0:
            # Recusa um custo zerado ou negativo: melhor nascer bruto e deixar
            # a fatura corrigir do que gravar uma camada de valoração inválida
            _logger.warning(
                "l10n_br_stock_account_net_cost: custo líquido inválido (%s) "
                "para a movimentação %s, mantendo o custo bruto",
                net_price_unit,
                self.display_name,
            )
            return result

        return net_price_unit
