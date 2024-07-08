# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
#   Renato Lima <renato.lima@akretion.com.br>
# @ 2024 KMEE - www.kmee.com.br -
#   Diego Paradeda <diego.paradeda@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tools import float_compare
from odoo.tools.float_utils import float_round

from .test_l10n_br_purchase_stock import L10nBrPurchaseStockBase


class L10nBrPurchaseStockBase(L10nBrPurchaseStockBase):
    def setUp(self):
        super().setUp()
        self.lp_purchase_po = self.env.ref(
            "l10n_br_purchase_stock.lucro_presumido_po_only_products_1"
        ).copy()
        self.picking_ids = False

        self.stock_acc_id = self.env["account.account"].search(
            [("code", "=", "1.1.3.1.02")], limit=1
        )
        self.stock_input_acc_id = self.env["account.account"].search(
            [("code", "=", "1.1.9.0.01")], limit=1
        )
        self.stock_output_acc_id = self.env["account.account"].search(
            [("code", "=", "1.1.9.0.02")], limit=1
        )

    def test_purchase_order_lp_stock_price_(self):
        """Test stock price compute in purchase order line."""

        purchase = self.lp_purchase_po
        self._change_user_company(self.company_lucro_presumido)
        self._run_purchase_order_onchanges(purchase)

        line1 = purchase.order_line[0]
        line2 = purchase.order_line[1]

        # line 1 -> 90.03
        line1.icms_tax_is_creditable = True
        line1.ipi_tax_is_creditable = True
        line1.cofins_tax_is_creditable = True
        line1.pis_tax_is_creditable = True
        line1._compute_stock_price_br()

        # price_precision = self.env["decimal.precision"].precision_get("Product Price")
        price_precision = self.env["decimal.precision"].precision_get("Product Price")
        expected_stock_price = float_round(
            (
                (
                    line1.amount_total
                    - line1.ipi_value
                    - line1.icms_value
                    - line1.pis_value
                    - line1.cofins_value
                )
                / line1.product_qty
            ),
            precision_digits=price_precision,
        )
        computed_stock_price = line1.stock_price_br

        compare = float_compare(
            expected_stock_price, computed_stock_price, precision_digits=price_precision
        )
        self.assertEqual(
            compare,
            0,
            f"Stock value mispriced - comercialização\nexpected: \
                {expected_stock_price}\ncomputed: {computed_stock_price}",
        )

        # line 2 -> 120.75 (price with taxes)
        line2.icms_tax_is_creditable = False
        line2.ipi_tax_is_creditable = False
        line2.cofins_tax_is_creditable = False
        line2.pis_tax_is_creditable = False
        line2._compute_stock_price_br()
        expected_stock_price = float_round(
            line2.amount_total / line2.product_qty, precision_digits=price_precision
        )
        computed_stock_price = line2.stock_price_br

        compare = float_compare(
            expected_stock_price, computed_stock_price, precision_digits=price_precision
        )
        self.assertEqual(
            compare,
            0,
            f"Stock value mispriced - industrialização\nexpected: \
                {expected_stock_price}\ncomputed: {computed_stock_price}",
        )

        purchase.button_confirm()

        # Test if product cost matches stock price. Requires AVCO and auto stock valuation.
        self.picking_id = purchase.picking_ids

        # product categories
        product_id1 = self.po_products.order_line[0].product_id
        categ_id1 = product_id1.categ_id

        categ_id1.write(
            {
                "property_stock_valuation_account_id": self.stock_acc_id.id,
                "property_stock_account_input_categ_id": self.stock_input_acc_id.id,
                "property_stock_account_output_categ_id": self.stock_output_acc_id.id,
                "property_valuation": "real_time",
                "property_cost_method": "average",
            }
        )

        self.assertEqual(
            categ_id1.property_stock_valuation_account_id.code,
            "1.1.3.1.02",
            "Invalid account in product category!",
        )
        self.assertEqual(
            categ_id1.property_stock_account_input_categ_id.code,
            "1.1.9.0.01",
            "Invalid account in product category!",
        )
        self.assertEqual(
            categ_id1.property_stock_account_output_categ_id.code,
            "1.1.9.0.02",
            "Invalid account in product category!",
        )

        # Validate picking
        self.picking_id.action_confirm()
        self.picking_id.action_assign()
        # Force picking qties and validate
        for move in self.picking_id.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        self.picking_id.button_validate()
