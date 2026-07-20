# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestStockCostImport(TransactionCase):
    """RF-H1: produto CRIADO no import de NF-e recebe standard_price = custo
    de aquisição líquido da linha (stock_cost_unit), não o vUnCom bruto.

    O método é testado diretamente sobre um documento fiscal com valores
    reais (o demo de compra tem ICMS destacado), pois o XML de teste do
    módulo tem impostos zerados — nele bruto e líquido coincidem."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company
        cls.edoc = cls.env.ref("l10n_br_fiscal.demo_nfe_purchase_same_state")
        cls.line = cls.env.ref(
            "l10n_br_fiscal.demo_nfe_purchase_line_same_state_1-1"
        )
        cls.wizard = cls.env["l10n_br_fiscal.document.import.wizard"].create(
            {"company_id": cls.company.id}
        )

    def test_new_product_gets_net_cost(self):
        """Produto criado na mesma transação do import: standard_price passa
        do bruto para o custo líquido da linha."""
        new_product = self.env["product.product"].create(
            {
                "name": "Produto novo do import",
                "standard_price": self.line.price_unit,  # vUnCom bruto
            }
        )
        self.line.product_id = new_product
        self.line._compute_stock_cost_unit()
        self.assertGreater(self.line.icms_value, 0)
        self.assertLess(self.line.stock_cost_unit, self.line.price_unit)

        self.wizard._update_new_products_standard_price(self.edoc)

        self.assertAlmostEqual(
            new_product.standard_price, self.line.stock_cost_unit, places=2
        )

    def test_existing_product_untouched(self):
        """Produto pré-existente (create_date anterior ao documento): o
        custo é gerido pela valorização — o import não o altera."""
        product = self.line.product_id  # produto demo, criado na instalação
        old_price = 123.45
        product.standard_price = old_price

        self.wizard._update_new_products_standard_price(self.edoc)

        self.assertAlmostEqual(product.standard_price, old_price, places=2)
