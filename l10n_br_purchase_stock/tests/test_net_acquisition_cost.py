# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Custo liquido de aquisicao ao longo do ciclo completo de compra.

Pedido, recebimento, fatura e **confirmacao da fatura**. O ultimo passo e o
que importa: e nele que `purchase_stock` chama `_apply_price_difference()`,
compara a camada de valoracao contra o preco da linha da fatura e, se houver
diferenca, grava uma camada de correcao.

Enquanto essa comparacao usa o preco bruto, ela devolve ao estoque exatamente
o imposto recuperavel que o custo liquido tirou - silenciosamente, numa camada
filha que ninguem abre. Por isso todo cenario aqui afirma sobre o razao depois
da confirmacao, e nao sobre o custo calculado no recebimento.
"""

import logging
import unittest

from odoo import fields
from odoo.tests import Form

from odoo.addons.l10n_br_stock_account.tests.common import TestBrPickingInvoicingCommon

_logger = logging.getLogger(__name__)

# Contas do l10n_br_coa_generic
ACCOUNT_BRIDGE = "1.1.9.0.01"  # Estoque Intermediario (Recebido)
ACCOUNT_STOCK = "1.1.3.1.02"  # Compras Mercadorias
ACCOUNT_COGS = "5.1.1.1.01"  # Custo das Mercadorias Vendidas
PREFIX_RECOVERABLE = "1.1.4.1."  # <Imposto> a Compensar

SIMPLES_FRAMEWORKS = ("1", "4")


class TestNetAcquisitionCost(TestBrPickingInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.company = cls.env.ref(
            "l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False
        )
        if not cls.company:
            raise unittest.SkipTest("Requer os dados de demonstracao do l10n_br_base.")
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company

        # Fornecedor do regime normal de proposito: um fornecedor do Simples
        # nao transfere credito de ICMS (LC 123/2006, art. 23), so o destacado
        # sob CSOSN 101/201. Medir creditabilidade contra ele daria baseline
        # errada.
        cls.supplier = cls.env.ref("l10n_br_base.res_partner_intel")
        if cls.supplier.tax_framework in SIMPLES_FRAMEWORKS:
            raise unittest.SkipTest(
                "O fornecedor da fixture e do Simples Nacional; o credito de "
                "ICMS nao existe nesse caso."
            )

        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.fiscal_operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")

        cls.account_bridge = cls._find_account(ACCOUNT_BRIDGE)
        cls.account_stock = cls._find_account(ACCOUNT_STOCK)
        cls.account_cogs = cls._find_account(ACCOUNT_COGS)
        cls.accounts_recoverable = cls.env["account.account"].search(
            [
                ("code", "=like", PREFIX_RECOVERABLE + "%"),
                ("company_id", "=", cls.company.id),
            ]
        )
        cls.product = cls._build_product()

    # ------------------------------------------------------------------
    # Fixture
    # ------------------------------------------------------------------

    @classmethod
    def _find_account(cls, code):
        account = cls.env["account.account"].search(
            [("code", "=", code), ("company_id", "=", cls.company.id)], limit=1
        )
        if not account:
            raise unittest.SkipTest(
                "Conta %s ausente: a fixture espera o l10n_br_coa_generic." % code
            )
        return account

    @classmethod
    def _build_product(cls):
        """Produto em categoria AVCO com avaliacao automatica.

        A localizacao nao entrega nenhuma categoria assim, e sem ela o ajuste
        de diferenca de preco nem chega a rodar - o custo liquido passaria no
        teste sem nunca ter sido posto a prova. O produto e copia de um de
        demonstracao, para herdar NCM, genero fiscal e origem do ICMS.
        """
        journal = cls.env["account.journal"].search(
            [("code", "=", "STJ"), ("company_id", "=", cls.company.id)], limit=1
        ) or cls.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", cls.company.id)], limit=1
        )
        if not journal:
            raise unittest.SkipTest("Nenhum diario de estoque na empresa.")
        category = (
            cls.env["product.category"]
            .with_company(cls.company)
            .create(
                {
                    "name": "Custo Liquido de Aquisicao (AVCO / Automated)",
                    "property_cost_method": "average",
                    "property_valuation": "real_time",
                    "property_stock_account_input_categ_id": cls.account_bridge.id,
                    "property_stock_account_output_categ_id": cls.account_bridge.id,
                    "property_stock_valuation_account_id": cls.account_stock.id,
                    "property_account_expense_categ_id": cls.account_cogs.id,
                    "property_stock_journal": journal.id,
                }
            )
        )
        return (
            cls.env.ref("product.product_product_12")
            .with_company(cls.company)
            .copy(
                {
                    "name": "Produto Custo Liquido (AVCO + Avaliacao Automatica)",
                    "default_code": "TEST-NET-COST",
                    "categ_id": category.id,
                    "detailed_type": "product",
                    "purchase_ok": True,
                    "standard_price": 0.0,
                    "seller_ids": [(5, 0, 0)],
                }
            )
        )

    # ------------------------------------------------------------------
    # Medidas
    # ------------------------------------------------------------------

    def _balance(self, accounts):
        self.env.flush_all()
        lines = self.env["account.move.line"].search(
            [
                ("account_id", "in", accounts.ids),
                ("parent_state", "=", "posted"),
                ("company_id", "=", self.company.id),
            ]
        )
        return round(sum(lines.mapped("balance")), 2)

    def _snapshot(self):
        layers = self.env["stock.valuation.layer"].search(
            [("product_id", "=", self.product.id)]
        )
        return {
            "bridge": self._balance(self.account_bridge),
            "stock": self._balance(self.account_stock),
            "cogs": self._balance(self.account_cogs),
            "recoverable": self._balance(self.accounts_recoverable),
            "svl": round(sum(layers.mapped("value")), 2),
        }

    def _bill_net_on_line_account(self, bill):
        """Quanto a fatura debita, no total, na conta das linhas de produto.

        Escrito de forma independente de `_get_stock_valuation_amount`, para o
        teste nao virar tautologia do codigo que ele verifica.
        """
        product_lines = bill.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        accounts = product_lines.mapped("account_id")
        tax_lines = bill.line_ids.filtered(
            lambda line: line.tax_line_id and line.account_id in accounts
        )
        return round(
            sum(product_lines.mapped("amount_currency"))
            + sum(tax_lines.mapped("amount_currency")),
            2,
        )

    def _bill_recoverable(self, bill):
        tax_lines = bill.line_ids.filtered(
            lambda line: line.tax_line_id
            and line.account_id in self.accounts_recoverable
        )
        return round(sum(tax_lines.mapped("amount_currency")), 2)

    def _set_deductible_taxes(self, value):
        self.fiscal_operation.with_company(self.company).deductible_taxes = value

    # ------------------------------------------------------------------
    # Fluxo
    # ------------------------------------------------------------------

    def _run_cycle(self, price, bill_price=None):
        before = self._snapshot()

        order_form = Form(self.env["purchase.order"].with_company(self.company))
        order_form.partner_id = self.supplier
        order_form.fiscal_operation_id = self.fiscal_operation
        with order_form.order_line.new() as line:
            line.product_id = self.product
            line.fiscal_operation_line_id = self.fiscal_operation_line
            line.product_qty = 1.0
            line.price_unit = price
        order = order_form.save()
        order.button_confirm()

        picking = order.picking_ids
        self.assertTrue(picking, "O pedido nao gerou recebimento.")
        self.picking_move_state(picking)
        receipt_layers = picking.move_ids.stock_valuation_layer_ids
        receipt_value = round(sum(receipt_layers.mapped("value")), 2)

        order.action_create_invoice()
        bill = order.invoice_ids
        bill.ensure_one()
        bill.invoice_date = fields.Date.context_today(bill)
        if bill_price is not None:
            bill.invoice_line_ids.filtered(
                lambda line: line.display_type == "product"
            ).write({"price_unit": bill_price})
        bill.action_post()

        after = self._snapshot()
        pdiff = self.env["stock.valuation.layer"].search(
            [("stock_valuation_layer_id", "in", receipt_layers.ids)]
        )
        return {
            "bill": bill,
            "receipt_value": receipt_value,
            "pdiff_value": round(sum(pdiff.mapped("value")), 2),
            "bill_net": self._bill_net_on_line_account(bill),
            "bill_recoverable": self._bill_recoverable(bill),
            "delta": {k: round(after[k] - before[k], 2) for k in before},
        }

    def _assert_ledger_closes(self, result, scenario):
        """O nucleo: a ponte fecha e o estoque vale o liquido da fatura."""
        delta = result["delta"]
        _logger.info(
            "%s | ponte %.2f | estoque %.2f | svl %.2f | a compensar %.2f "
            "| liquido da fatura %.2f | passo 3 %.2f",
            scenario,
            delta["bridge"],
            delta["stock"],
            delta["svl"],
            delta["recoverable"],
            result["bill_net"],
            result["pdiff_value"],
        )
        self.assertAlmostEqual(
            delta["bridge"],
            0.0,
            places=2,
            msg="%s: a conta ponte nao fechou (sobrou %.2f). O recebimento "
            "creditou o bruto e a fatura debitou o liquido, e nada cobriu a "
            "diferenca." % (scenario, delta["bridge"]),
        )
        self.assertAlmostEqual(
            delta["svl"],
            result["bill_net"],
            places=2,
            msg="%s: o estoque vale %.2f, mas a fatura debitou %.2f na conta "
            "da linha. A diferenca de %.2f e o imposto recuperavel que voltou "
            "ao custo na confirmacao da fatura."
            % (
                scenario,
                delta["svl"],
                result["bill_net"],
                delta["svl"] - result["bill_net"],
            ),
        )
        self.assertAlmostEqual(
            delta["stock"],
            result["bill_net"],
            places=2,
            msg="%s: a conta de estoque divergiu da camada de valoracao." % scenario,
        )
        self.assertAlmostEqual(
            delta["recoverable"],
            result["bill_recoverable"],
            places=2,
            msg="%s: o credito nao chegou as contas a compensar." % scenario,
        )
        self.assertAlmostEqual(
            delta["cogs"],
            0.0,
            places=2,
            msg="%s: sobrou %.2f no resultado num ciclo sem venda - o produto "
            "foi contado no estoque e no resultado ao mesmo tempo."
            % (scenario, delta["cogs"]),
        )

    # ------------------------------------------------------------------
    # Cenarios
    # ------------------------------------------------------------------

    def test_deductible_taxes_off(self):
        """Impostos dedutiveis desligados: o default de fabrica da operacao."""
        self._set_deductible_taxes(False)
        result = self._run_cycle(price=100.0)
        self.assertGreater(
            result["bill_recoverable"],
            0.0,
            "A fatura nao creditou imposto nenhum: o cenario nao testa nada.",
        )
        self._assert_ledger_closes(result, "dedutiveis OFF")

    def test_deductible_taxes_on(self):
        """Impostos dedutiveis ligados: o imposto ganha linhas proprias."""
        self._set_deductible_taxes(True)
        result = self._run_cycle(price=100.0)
        self._assert_ledger_closes(result, "dedutiveis ON")

    def test_deductible_taxes_flag_does_not_change_balances(self):
        """A flag muda a apresentacao da fatura, nunca o resultado contabil."""
        self._set_deductible_taxes(False)
        off = self._run_cycle(price=100.0)
        self._set_deductible_taxes(True)
        on = self._run_cycle(price=100.0)
        for key in ("bridge", "stock", "svl", "recoverable"):
            self.assertAlmostEqual(
                on["delta"][key],
                off["delta"][key],
                places=2,
                msg="deductible_taxes mudou o saldo de %s: %.2f com a flag "
                "ligada contra %.2f com ela desligada. A flag decide como o "
                "imposto aparece na fatura, nao quanto vale o estoque."
                % (key, on["delta"][key], off["delta"][key]),
            )

    def test_real_price_difference_still_applies(self):
        """O ajuste de diferenca de preco continua vivo e continua correto.

        Pedido a 100, fatura a 110. A correcao tem que ser a distancia entre a
        camada e o liquido da fatura - nunca o valor do imposto, que e o que
        ela lanca quando a base da comparacao e o preco bruto.
        """
        self._set_deductible_taxes(False)
        result = self._run_cycle(price=100.0, bill_price=110.0)
        expected = round(result["bill_net"] - result["receipt_value"], 2)
        self.assertAlmostEqual(
            result["pdiff_value"],
            expected,
            places=2,
            msg="A correcao foi %.2f, esperada %.2f (liquido da fatura %.2f "
            "menos camada do recebimento %.2f)."
            % (
                result["pdiff_value"],
                expected,
                result["bill_net"],
                result["receipt_value"],
            ),
        )
        self.assertNotAlmostEqual(
            abs(result["pdiff_value"]),
            abs(result["bill_recoverable"]),
            places=2,
            msg="A correcao foi igual ao imposto recuperavel (%.2f): sinal de "
            "que a comparacao voltou a usar o preco bruto."
            % result["bill_recoverable"],
        )
        self._assert_ledger_closes(result, "pedido 100 / fatura 110")

    def test_tax_without_account_stays_in_cost(self):
        """Quem decide creditabilidade e o plano de contas.

        Um imposto sem conta na linha de repartição cai na conta da linha base
        e continua no custo - mesma convencao que o core usa em `total_void`.
        Sem lista de CST nem regra de regime em codigo.
        """
        self._set_deductible_taxes(False)
        icms = self.env["account.tax"].search(
            [
                ("type_tax_use", "=", "purchase"),
                ("deductible", "=", False),
                ("company_id", "=", self.company.id),
                ("tax_group_id.fiscal_tax_group_id.tax_domain", "=", "icms"),
            ],
            limit=1,
        )
        self.assertTrue(icms, "Imposto contabil de ICMS de entrada nao encontrado.")
        repartition = icms.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )
        self.assertTrue(
            repartition.account_id, "O ICMS Entrada ja estava sem conta de credito."
        )

        self._set_deductible_taxes(False)
        with_credit = self._run_cycle(price=100.0)

        repartition.account_id = False
        without_credit = self._run_cycle(price=100.0)

        self._assert_ledger_closes(without_credit, "ICMS sem conta de credito")
        self.assertGreater(
            without_credit["delta"]["svl"],
            with_credit["delta"]["svl"],
            "Tirar a conta de credito do ICMS tinha que deixar o imposto no "
            "custo, elevando o valor do estoque.",
        )
        self.assertLess(
            without_credit["delta"]["recoverable"],
            with_credit["delta"]["recoverable"],
            "O ICMS continuou indo para conta de credito mesmo sem conta na "
            "linha de repartição.",
        )
