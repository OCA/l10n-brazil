# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Base da suite: fixture, fluxo unico de compra e relatorio do razao.

A suite e uma regua neutra: roda igual contra a 16.0 limpa, contra o PR #3819
e contra os PRs #4964-#4967, porque nao referencia nenhum campo introduzido
por esses PRs. Todos os asserts sao sobre o que ja existe hoje - camadas de
valoracao, linhas de lancamento e saldos de conta.
"""

import logging
import unittest

from odoo import fields
from odoo.tests import Form

from odoo.addons.l10n_br_stock_account.tests.common import TestBrPickingInvoicingCommon

_logger = logging.getLogger(__name__)

# Contas do l10n_br_coa_generic usadas em todas as medidas
ACCOUNT_BRIDGE = "1.1.9.0.01"  # Estoque Intermediario (Recebido)
ACCOUNT_STOCK = "1.1.3.1.02"  # Compras Mercadorias
ACCOUNT_COGS = "5.1.1.1.01"  # Custo das Mercadorias Vendidas
PREFIX_RECOVERABLE = "1.1.4.1."  # <Imposto> a Compensar
ACCOUNT_ICMS_RECOVERABLE = "1.1.4.1.02"  # ICMS a Compensar

PRODUCT_NAME = "Produto Teste Creditabilidade (AVCO + Avaliacao Automatica)"
PRODUCT_CODE = "TEST-AVCO-CRED"
CATEGORY_NAME = "Teste Creditabilidade (AVCO / Automated)"


class CycleResult:
    """O que um ciclo compra -> recebimento -> fatura -> confirmar produziu."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @property
    def delta(self):
        return {
            key: round(self.after[key] - self.before[key], 2) for key in self.before
        }


class TestCreditabilityCommon(TestBrPickingInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.company = cls.env.ref(
            "l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False
        )
        if not cls.company:
            raise unittest.SkipTest(
                "A suite espera a empresa de demonstracao "
                "l10n_br_base.empresa_lucro_presumido. Carregue a base com "
                "dados de demonstracao."
            )
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company

        # NAO usar o `res_partner_akretion` dos pedidos de demonstracao: ele e
        # Simples Nacional, e um fornecedor do Simples nao transfere credito de
        # ICMS (LC 123/2006, art. 23) - so o destacado sob CSOSN 101/201. Medir
        # creditabilidade de ICMS contra um fornecedor desses da baseline
        # errada e entrega uma refutacao facil a quem for questionado.
        cls.supplier = cls.env.ref("l10n_br_base.res_partner_intel")
        if cls.supplier.tax_framework in ("1", "4"):
            raise unittest.SkipTest(
                "O fornecedor da fixture (%s) e do Simples Nacional. A suite "
                "precisa de um fornecedor do regime normal para o credito de "
                "ICMS existir." % cls.supplier.name
            )
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.fiscal_operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")

        cls.account_bridge = cls._find_account(ACCOUNT_BRIDGE)
        cls.account_stock = cls._find_account(ACCOUNT_STOCK)
        cls.account_cogs = cls._find_account(ACCOUNT_COGS)
        cls.account_icms = cls._find_account(ACCOUNT_ICMS_RECOVERABLE)
        cls.accounts_recoverable = cls.env["account.account"].search(
            [
                ("code", "=like", PREFIX_RECOVERABLE + "%"),
                ("company_id", "=", cls.company.id),
            ]
        )

        cls.category = cls._build_category()
        cls.product = cls._build_product()
        cls._enable_known_opt_ins()

    @classmethod
    def _enable_known_opt_ins(cls):
        """Liga o opt-in de custo liquido da estrategia sob teste, se existir.

        Nao quebra a neutralidade: nao ha assert nenhum sobre esses campos, e
        a suite roda igual quando eles nao existem. So evita medir um PR
        desligado - o #4967, por exemplo, so valoriza pelo custo liquido
        quando `stock_valuation_via_stock_price` esta ligado na empresa.
        """
        for field_name in ("stock_valuation_via_stock_price",):
            if field_name in cls.env["res.company"]._fields:
                cls.company.write({field_name: True})
                _logger.info(
                    "opt-in da estrategia sob teste ligado: res.company.%s",
                    field_name,
                )

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
                f"Conta {code} nao encontrada na empresa {cls.company.name}. "
                "A suite espera o plano de contas l10n_br_coa_generic."
            )
        return account

    @classmethod
    def _find_stock_journal(cls):
        journal = cls.env["account.journal"].search(
            [("code", "=", "STJ"), ("company_id", "=", cls.company.id)], limit=1
        )
        if not journal:
            journal = cls.env["account.journal"].search(
                [("type", "=", "general"), ("company_id", "=", cls.company.id)],
                limit=1,
            )
        if not journal:
            raise unittest.SkipTest(
                "Nenhum diario de estoque na empresa %s." % cls.company.name
            )
        return journal

    @classmethod
    def _build_category(cls):
        """AVCO + avaliacao automatica.

        A localizacao nao entrega nenhuma categoria assim, e sem ela o ajuste
        de diferenca de preco (o "passo 3") nem chega a rodar.
        """
        return (
            cls.env["product.category"]
            .with_company(cls.company)
            .create(
                {
                    "name": CATEGORY_NAME,
                    "property_cost_method": "average",
                    "property_valuation": "real_time",
                    "property_stock_account_input_categ_id": cls.account_bridge.id,
                    "property_stock_valuation_account_id": cls.account_stock.id,
                    "property_stock_account_output_categ_id": cls.account_bridge.id,
                    "property_account_expense_categ_id": cls.account_cogs.id,
                    "property_stock_journal": cls._find_stock_journal().id,
                }
            )
        )

    @classmethod
    def _build_product(cls):
        """Copia um produto de demonstracao para herdar o cadastro fiscal.

        Copiar traz NCM, genero fiscal e origem do ICMS - inclusive os valores
        company_dependent, porque a copia roda no contexto da empresa.
        """
        return (
            cls.env.ref("product.product_product_12")
            .with_company(cls.company)
            .copy(
                {
                    "name": PRODUCT_NAME,
                    "default_code": PRODUCT_CODE,
                    "categ_id": cls.category.id,
                    "detailed_type": "product",
                    "purchase_ok": True,
                    "standard_price": 0.0,
                    "seller_ids": [(5, 0, 0)],
                }
            )
        )

    # ------------------------------------------------------------------
    # Snapshot e oraculos
    # ------------------------------------------------------------------

    def _account_balance(self, accounts):
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
            "bridge": self._account_balance(self.account_bridge),
            "stock": self._account_balance(self.account_stock),
            "cogs": self._account_balance(self.account_cogs),
            "recoverable": self._account_balance(self.accounts_recoverable),
            "icms": self._account_balance(self.account_icms),
            "svl": round(sum(layers.mapped("value")), 2),
        }

    def _bill_net_on_line_account(self, bill):
        """Quanto a fatura debita, no total, na conta das linhas de produto.

        Oraculo independente do motor de custo: soma o valor das linhas de
        produto com as linhas de imposto que foram para a mesma conta. E o que
        efetivamente sobra para o estoque depois dos creditos tomados.
        """
        product_lines = bill.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        accounts = product_lines.mapped("account_id")
        total = sum(product_lines.mapped("amount_currency"))
        tax_lines = bill.line_ids.filtered(
            lambda line: line.tax_line_id and line.account_id in accounts
        )
        return round(total + sum(tax_lines.mapped("amount_currency")), 2)

    def _bill_recoverable_taxes(self, bill):
        """Impostos que a fatura levou para contas de credito (a Compensar)."""
        tax_lines = bill.line_ids.filtered(
            lambda line: line.tax_line_id
            and line.account_id in self.accounts_recoverable
        )
        return round(sum(tax_lines.mapped("amount_currency")), 2)

    # ------------------------------------------------------------------
    # Fluxo unico
    # ------------------------------------------------------------------

    def _run_cycle(
        self, price, bill_price=None, via_wizard=False, qty=1.0, operation_line=None
    ):
        """compra -> recebimento -> fatura -> CONFIRMAR A FATURA.

        O ultimo passo e o que falta nos testes existentes: e nele que o core
        dispara `_apply_price_difference()` e pode desfazer o custo liquido.
        """
        before = self._snapshot()

        order_form = Form(self.env["purchase.order"].with_company(self.company))
        order_form.partner_id = self.supplier
        order_form.fiscal_operation_id = self.fiscal_operation
        with order_form.order_line.new() as line:
            line.product_id = self.product
            line.fiscal_operation_line_id = operation_line or self.fiscal_operation_line
            line.product_qty = qty
            line.price_unit = price
        order = order_form.save()
        order.button_confirm()

        picking = order.picking_ids
        self.assertTrue(picking, "O pedido nao gerou recebimento.")
        if via_wizard:
            self._ensure_fiscal_operation_journal()
            picking.set_to_be_invoiced()
        self.picking_move_state(picking)

        receipt_layers = picking.move_ids.stock_valuation_layer_ids
        # Retrato logo depois do recebimento, antes de a fatura existir: e a
        # foto que separa "o recebimento valorou certo" de "a valoracao
        # sobreviveu a confirmacao da fatura"
        after_receipt = self._snapshot()
        receipt_value_before_bill = round(sum(receipt_layers.mapped("value")), 2)

        if via_wizard:
            bill = self.create_invoice_wizard(picking)
        else:
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
        pdiff_layers = self.env["stock.valuation.layer"].search(
            [
                ("product_id", "=", self.product.id),
                ("stock_valuation_layer_id", "in", receipt_layers.ids),
            ]
        )
        return CycleResult(
            order=order,
            picking=picking,
            bill=bill,
            receipt_layers=receipt_layers,
            pdiff_layers=pdiff_layers,
            receipt_value=receipt_value_before_bill,
            after_receipt=after_receipt,
            svl_after_receipt=after_receipt["svl"] - before["svl"],
            svl_after_bill=after["svl"] - before["svl"],
            pdiff_value=round(sum(pdiff_layers.mapped("value")), 2),
            bill_net=self._bill_net_on_line_account(bill),
            bill_recoverable=self._bill_recoverable_taxes(bill),
            before=before,
            after=after,
        )

    def _ensure_fiscal_operation_journal(self):
        """O assistente de faturamento pelo picking exige diario na operacao.

        Os dados de demonstracao nao preenchem `journal_id` da operacao Compras
        para a Lucro Presumido, e o campo e company_dependent - entao a
        atribuicao volta atras junto com a transacao.
        """
        operation = self.fiscal_operation.with_company(self.company)
        if operation.journal_id:
            return
        journal = self.env["account.journal"].search(
            [("type", "=", "purchase"), ("company_id", "=", self.company.id)],
            limit=1,
        )
        self.assertTrue(
            journal, "Nenhum diario de compras na empresa %s." % self.company.name
        )
        operation.journal_id = journal

    def _set_deductible_taxes(self, value):
        self.fiscal_operation.with_company(self.company).deductible_taxes = value

    # ------------------------------------------------------------------
    # Relatorio
    # ------------------------------------------------------------------

    def _diagnostics(self, result):
        """Linhas extras de diagnostico, sem assert.

        Le campos que so existem em alguns PRs. Nunca afirma sobre eles: serve
        para a tabela ficar mais informativa quando a suite roda no PR do
        Renato ou do mileo.
        """
        product_lines = result.bill.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        gross = round(sum(product_lines.mapped("price_subtotal")), 2)
        rate = (result.bill_recoverable / gross * 100) if gross else 0.0
        bridge_after_receipt = result.after_receipt["bridge"] - result.before["bridge"]
        bridge_after_bill = result.after["bridge"] - result.before["bridge"]
        lines = [
            f"fornecedor {self.supplier.name} "
            f"(tax_framework={self.supplier.tax_framework})",
            f"fatura {result.bill.name}: bruto {gross:.2f}, "
            f"creditavel {result.bill_recoverable:.2f} ({rate:.2f}%), "
            f"liquido {result.bill_net:.2f}",
            f"camada apos o RECEBIMENTO: {result.svl_after_receipt:.2f}"
            f"  ->  apos CONFIRMAR A FATURA: {result.svl_after_bill:.2f}",
            f"ponte apos o RECEBIMENTO: {bridge_after_receipt:.2f}"
            f"  ->  apos CONFIRMAR A FATURA: {bridge_after_bill:.2f}",
        ]
        move = result.picking.move_ids[:1]
        for field_name in ("cost_unit", "valuation_via_stock_price"):
            if move and field_name in move._fields:
                lines.append(f"{field_name} no stock.move: {move[field_name]}")
        for layer in result.receipt_layers:
            lines.append(
                f"camada do recebimento {layer.id}: value={layer.value:.2f} "
                f"remaining_value={layer.remaining_value:.2f}"
            )
        for layer in result.pdiff_layers:
            lines.append(f"passo 3 criou camada {layer.id}: value={layer.value:.2f}")
        if not result.pdiff_layers:
            lines.append("passo 3 nao criou camada nenhuma")
        return lines

    def check_ledger(self, scenario, checks, result=None):
        """Loga a tabela sempre, e falha uma vez so com a tabela na mensagem.

        `checks` e uma lista de (medida, esperado, obtido). Falhar de uma vez
        com o quadro inteiro e proposital: o retrato completo vale mais como
        argumento do que o primeiro assert que quebra.
        """
        rows = []
        failed = []
        for label, expected, actual in checks:
            expected = round(expected, 2)
            actual = round(actual, 2)
            ok = abs(expected - actual) < 0.005
            if not ok:
                failed.append(label)
            rows.append(
                "  {:<44}{:>11}{:>11}{:>11}  {}".format(
                    label,
                    "%.2f" % expected,
                    "%.2f" % actual,
                    "%+.2f" % (actual - expected),
                    "ok" if ok else "FALHOU",
                )
            )

        table = [
            "",
            "\u2501" * 90,
            "  CENARIO: %s" % scenario,
            "\u2501" * 90,
            "  {:<44}{:>11}{:>11}{:>11}".format("medida", "esperado", "obtido", "dif"),
            "  " + "\u2500" * 86,
        ]
        table += rows
        if result is not None:
            table.append("  " + "\u2500" * 86)
            table += ["  [diag] %s" % line for line in self._diagnostics(result)]
        table.append("\u2501" * 90)
        rendered = "\n".join(table)

        _logger.info("%s", rendered)
        if failed:
            raise self.failureException(
                rendered
                + "\n\n%d de %d medidas fora do esperado: %s"
                % (len(failed), len(checks), ", ".join(failed))
            )
