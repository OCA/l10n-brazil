# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    PROFIT_CALCULATION_PRESUMED,
    PROFIT_CALCULATION_REAL,
    TAX_FRAMEWORK_NORMAL,
    TAX_FRAMEWORK_SIMPLES,
)

from odoo.tests import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestStockCostDeductible(AccountMoveBRCommon):
    """Fase F — lançamento composto por fórmulas (RF-F0/F0b/F0c/F1b).

    A fatura de fornecedor gera o lançamento da escrituração clássica, cuja
    FÓRMULA deriva do resolvedor de creditabilidade (regime x destinação x
    fornecedor):

    * imposto creditável: variante normal (Db "a Compensar") + dedutível
      (Cr na conta da própria linha do produto — repartição -100 sem conta)
      → custo líquido formado na conta certa;
    * imposto NÃO creditável por dentro (ICMS/PIS/COFINS): nenhuma variante
      contábil — o valor permanece no custo;
    * imposto NÃO creditável por fora (IPI): variante "s/ Crédito" (par
      +100/-100 sem contas → amount 0; o valor compõe o total da fatura).

    Sem ``product_destination`` na operação, comportamento histórico.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()
        cls.fo_compras = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.fo_compras.deductible_taxes = True
        cls.fo_compras_compras = cls.env.ref("l10n_br_fiscal.fo_compras_compras")
        # O perfil fiscal default de parceiros demo é Simples (SNC); para os
        # testes de crédito o fornecedor precisa ser contribuinte normal.
        cls.partner_a.tax_framework = TAX_FRAMEWORK_NORMAL
        # Empresa do common: framework 3; garantir presumido não-industrial
        # como ponto de partida.
        cls.env.company.write(
            {
                "profit_calculation": PROFIT_CALCULATION_PRESUMED,
                "is_industry": False,
                "ripi": False,
            }
        )

    def _bill(self):
        return self.init_invoice(
            "in_invoice",
            products=[self.product_a],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=self.fo_compras,
            fiscal_operation_lines=[self.fo_compras_compras],
            document_serie="1",
            document_number="123",
        )

    @staticmethod
    def _names(taxes):
        return sorted(taxes.mapped("name"))

    def test_presumido_formula(self):
        """Presumido comercial: ICMS credita (par normal+dedutível);
        PIS/COFINS por dentro sem crédito (nenhuma variante); IPI por fora
        sem crédito (variante s/ Crédito)."""
        bill = self._bill()
        line = bill.invoice_line_ids
        taxes = line.tax_ids
        self.assertTrue(taxes.filtered(lambda t: "ICMS" in t.name and t.deductible))
        self.assertTrue(
            taxes.filtered(
                lambda t: "ICMS" in t.name and not t.deductible and not t.no_credit
            )
        )
        self.assertFalse(
            taxes.filtered(lambda t: "PIS" in t.name or "COFINS" in t.name),
            f"PIS/COFINS não creditam no Presumido: {self._names(taxes)}",
        )
        ipi_taxes = taxes.filtered(lambda t: "IPI" in t.name)
        self.assertTrue(ipi_taxes)
        self.assertTrue(
            all(t.no_credit for t in ipi_taxes),
            "IPI sem crédito deve usar apenas a variante s/ Crédito: "
            f"{self._names(ipi_taxes)}",
        )

    def test_presumido_posted_ledger(self):
        """Razão postado (Presumido): balanceia; nenhuma conta de dedução de
        receita ('s/ Vendas'); PIS/COFINS/IPI sem 'a Compensar'; o débito
        líquido na conta da linha = total - crédito de ICMS."""
        bill = self._bill()
        bill.action_post()
        line = bill.invoice_line_ids
        self.assertEqual(bill.state, "posted")

        product_account = line.account_id
        icms_value = line.icms_value
        self.assertGreater(icms_value, 0)

        for ml in bill.line_ids:
            self.assertNotIn(
                "Vendas",
                ml.account_id.name,
                f"compra não deve tocar conta de venda: {ml.account_id.name}",
            )
            if "Compensar" in ml.account_id.name:
                self.assertIn(
                    "ICMS",
                    ml.account_id.name,
                    "só o ICMS credita no Presumido comercial: "
                    f"{ml.account_id.name}",
                )
        product_lines = bill.line_ids.filtered(
            lambda ml: ml.account_id == product_account
        )
        net_debit = sum(product_lines.mapped("debit")) - sum(
            product_lines.mapped("credit")
        )
        self.assertAlmostEqual(
            net_debit,
            line.fiscal_amount_total - icms_value,
            places=2,
            msg="débito líquido na conta do produto = total - crédito ICMS",
        )

    def test_real_industrial_formula(self):
        """Lucro Real industrial: ICMS+IPI+PIS+COFINS creditam
        (par normal+dedutível para todos)."""
        self.env.company.write(
            {
                "profit_calculation": PROFIT_CALCULATION_REAL,
                "is_industry": True,
                "ripi": True,
            }
        )
        bill = self._bill()
        taxes = bill.invoice_line_ids.tax_ids
        for label in ("ICMS", "IPI", "PIS", "COFINS"):
            self.assertTrue(
                taxes.filtered(lambda t: label in t.name and t.deductible),
                f"{label} dedutível esperado no Real: {self._names(taxes)}",
            )
        self.assertFalse(taxes.filtered("no_credit"))

    def test_supplier_simples_formula(self):
        """Fornecedor do Simples: ICMS por dentro sem crédito (nenhuma
        variante), IPI s/ Crédito — mesmo com comprador Lucro Real."""
        self.env.company.write(
            {
                "profit_calculation": PROFIT_CALCULATION_REAL,
                "is_industry": True,
                "ripi": True,
            }
        )
        self.partner_a.tax_framework = TAX_FRAMEWORK_SIMPLES
        try:
            bill = self._bill()
            taxes = bill.invoice_line_ids.tax_ids
            self.assertFalse(
                taxes.filtered(lambda t: "ICMS" in t.name and t.deductible),
                "compra de Simples não credita ICMS",
            )
            ipi_taxes = taxes.filtered(lambda t: "IPI" in t.name)
            self.assertTrue(all(t.no_credit for t in ipi_taxes))
        finally:
            self.partner_a.tax_framework = TAX_FRAMEWORK_NORMAL

    def test_no_destination_keeps_legacy_behavior(self):
        """Sem destinação na operação: comportamento histórico (todas as
        variantes dedutíveis) — a granularidade é opt-in."""
        old_destination = self.fo_compras_compras.product_destination
        self.fo_compras_compras.product_destination = False
        try:
            bill = self._bill()
            taxes = bill.invoice_line_ids.tax_ids
            self.assertTrue(
                taxes.filtered(lambda t: "PIS" in t.name and t.deductible),
                "sem destinação o comportamento antigo é mantido: "
                f"{self._names(taxes)}",
            )
            self.assertFalse(taxes.filtered("no_credit"))
        finally:
            self.fo_compras_compras.product_destination = old_destination
