# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import tagged

from odoo.addons.l10n_br_fiscal.tests.operation_catalog_common import (
    OperationCatalogCommon,
)


@tagged("post_install", "-at_install", "op_catalog")
class TestCfopFlags(OperationCatalogCommon):
    """Saneamento dos flags finance_move/stock_move do CFOP.

    finance_move=1 gera lançamento financeiro (fatura); stock_move=1 movimenta
    estoque físico. Trava as correções de alta confiança (entrega futura +
    inconsistências interno×interestadual).
    """

    def _flags(self, num):
        cfop = self.env.ref(f"l10n_br_fiscal.cfop_{num}")
        return (cfop.finance_move, cfop.stock_move)

    def test_entrega_futura_faturamento(self):
        """Simples faturamento (5922): fatura, não move estoque -> 1/0."""
        for num in ("5922", "6922", "1922", "2922"):
            self.assertEqual(self._flags(num), (True, False), f"cfop_{num}")

    def test_entrega_futura_remessa(self):
        """Remessa entrega futura (5116/5117): move estoque, não fatura -> 0/1."""
        for num in ("5116", "6116", "5117", "6117", "1116", "2116", "1117", "2117"):
            self.assertEqual(self._flags(num), (False, True), f"cfop_{num}")

    def test_inconsistencia_interno_interestadual(self):
        """Mesma operação deve ter os mesmos flags em interno/interestadual/entrada."""
        # Devolução simbólica: 5919 alinhado aos pares (0/1).
        for num in ("5919", "6919", "1919", "2919"):
            self.assertEqual(self._flags(num), (False, True), f"cfop_{num}")
        # Devolução de transferência: 6208/6209 alinhados aos pares (0/1).
        for num in ("5208", "6208", "5209", "6209", "1208", "1209"):
            self.assertEqual(self._flags(num), (False, True), f"cfop_{num}")
