# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase


class L10nBRP7ModelInventoryReportTest(TransactionCase):
    """Test Brazilian P7 Model Inventory Report"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.p7_report_wizard = cls.env["l10n_br.p7.model.inventory.report.wizard"]

    def test_l10n_br_p7_model_inventory_report(self):
        """Test Brazilian P7 Model Inventory Report."""

        # Create Stock Valuation Layer
        # stock_picking_invoicing.stock_picking_invoicing_7
        picking = self.env.ref("stock_picking_invoicing.stock_picking_invoicing_7")
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity = move.product_uom_qty
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        wizard_obj = self.env["stock.invoice.onshipping"].with_context(
            active_ids=picking.ids,
            active_model=picking._name,
            active_id=picking.id,
            fiscal_operation_journal=False,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()

        wizard_obj = self.p7_report_wizard.with_context(
            default_compute_at_date=0,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.print_report()


class L10nBRP7ModelInventoryReportValueTest(TransactionCase):
    """Valor unitario e total do inventario P7 na data do relatorio."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.company
        cls.supplier_loc = cls.env.ref("stock.stock_location_suppliers")
        cls.stock_loc = (
            cls.env["stock.warehouse"]
            .search([("company_id", "=", cls.company.id)], limit=1)
            .lot_stock_id
        )
        cls.ncm = cls.env["l10n_br_fiscal.ncm"].search([], limit=1)

    def _create_product(self, name, cost_method="average"):
        categ = self.env["product.category"].create(
            {
                "name": f"P7 {name} {cost_method}",
                "property_cost_method": cost_method,
                "property_valuation": "manual_periodic",
            }
        )
        return self.env["product.product"].create(
            {
                "name": name,
                # Odoo 18: storable goods are consu products with is_storable
                "is_storable": True,
                "categ_id": categ.id,
                "ncm_id": self.ncm.id,
            }
        )

    def _receive(self, product, qty, price):
        move = self.env["stock.move"].create(
            {
                "name": product.name,
                "product_id": product.id,
                "product_uom": product.uom_id.id,
                "product_uom_qty": qty,
                "price_unit": price,
                "location_id": self.supplier_loc.id,
                "location_dest_id": self.stock_loc.id,
                "company_id": self.company.id,
            }
        )
        move._action_confirm()
        move._action_assign()
        move.quantity = qty
        # Odoo 18 only validates the picked moves when they are done
        move.picked = True
        move._action_done()

    def _report_line(self, product):
        wizard = self.env["l10n_br.p7.model.inventory.report.wizard"].create(
            {"date": fields.Datetime.now() + timedelta(hours=1)}
        )
        wizard = wizard.with_context(default_compute_at_date=0)
        lines, _total, _types = wizard.lines()
        for line in lines:
            if line["product_name"] == product.name:
                return line
        self.fail(f"Product {product.name} not in the P7 report")

    @staticmethod
    def _number(text):
        # "3.700,00" (pt_BR) or "3,700.00" (en_US) -> 3700.0
        text = text.strip()
        decimal_sep = max(text.rfind(","), text.rfind("."))
        integer = text[:decimal_sep].replace(".", "").replace(",", "")
        return float(f"{integer}.{text[decimal_sep + 1 :]}")

    def test_price_is_not_rounded_to_multiple_of_precision(self):
        """Custo 18,50 x 200 unidades deve dar 3.700,00 e nao 3.600,00."""
        product = self._create_product("P7 Item 18.50")
        self._receive(product, 200, 18.50)
        line = self._report_line(product)
        self.assertAlmostEqual(self._number(line["price_unit"]), 18.50, places=2)
        self.assertAlmostEqual(
            self._number(line["partial_total_value"]), 3700.00, places=2
        )

    def test_value_at_date_uses_all_valuation_layers_average(self):
        """Duas entradas (24 a 600 e 16 a 700): custo medio 640."""
        product = self._create_product("P7 Item Average")
        self._receive(product, 24, 600.0)
        self._receive(product, 16, 700.0)
        line = self._report_line(product)
        self.assertAlmostEqual(self._number(line["price_unit"]), 640.0, places=2)
        self.assertAlmostEqual(
            self._number(line["partial_total_value"]), 25600.0, places=2
        )

    def test_value_at_date_uses_all_valuation_layers_fifo(self):
        """Sem saidas, o saldo FIFO e o mesmo das duas entradas: 25.600."""
        product = self._create_product("P7 Item FIFO", cost_method="fifo")
        self._receive(product, 24, 600.0)
        self._receive(product, 16, 700.0)
        line = self._report_line(product)
        self.assertAlmostEqual(
            self._number(line["partial_total_value"]), 25600.0, places=2
        )
