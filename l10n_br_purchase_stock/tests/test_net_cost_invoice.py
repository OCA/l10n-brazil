# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNetCostSurvivesInvoice(TransactionCase):
    """Posting the vendor bill must not revert the net cost of the layer."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=[cls.company.id])
        )

        # A product of its own: a demo product would drag its stock in.
        cls.product = cls.env.ref("product.product_product_6").copy(
            {"name": "Net cost product (test)"}
        )
        cls.supplier = cls.env.ref("l10n_br_base.res_partner_intel")
        cls.supplier.tax_framework = "3"
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.fiscal_operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")

        valuation, bridge = (
            cls.env["account.account"].create(
                {
                    "name": name,
                    "code": code,
                    "account_type": "asset_current",
                    "company_id": cls.company.id,
                }
            )
            for name, code in (
                ("Stock valuation (test)", "TSTPSV"),
                ("Stock bridge (test)", "TSTPSB"),
            )
        )
        journal = cls.env["account.journal"].create(
            {
                "name": "Stock journal (test)",
                "code": "TSTPJ",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.product.categ_id.with_company(cls.company).write(
            {
                "property_stock_account_input_categ_id": bridge.id,
                "property_stock_account_output_categ_id": bridge.id,
                "property_stock_valuation_account_id": valuation.id,
                "property_stock_journal": journal.id,
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
            }
        )
        cls.company.stock_valuation_via_stock_price = True

    def _make_order(self, qty=1.0, price_unit=800.0):
        return (
            self.env["purchase.order"]
            .with_company(self.company)
            .create(
                {
                    "partner_id": self.supplier.id,
                    "company_id": self.company.id,
                    "fiscal_operation_id": self.fiscal_operation.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product.id,
                                "product_qty": qty,
                                "price_unit": price_unit,
                                "product_uom": self.product.uom_id.id,
                                "name": self.product.name,
                                "date_planned": fields.Datetime.now(),
                                "fiscal_operation_id": self.fiscal_operation.id,
                                "fiscal_operation_line_id": (
                                    self.fiscal_operation_line.id
                                ),
                            },
                        )
                    ],
                }
            )
        )

    def _receive(self):
        order = self._make_order()
        order.button_confirm()
        picking = order.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for line in picking.move_ids.move_line_ids:
            line.qty_done = line.reserved_uom_qty
        picking.with_context(skip_immediate=True, skip_backorder=True).button_validate()
        return order, picking.move_ids[0]

    def _bill(self, order):
        invoice = self.env["account.move"].browse(
            order.action_create_invoice()["res_id"]
        )
        invoice.invoice_date = fields.Date.today()
        return invoice

    def _product_layers(self):
        # The price difference layer hangs from the receipt layer and has no
        # stock move, so move.stock_valuation_layer_ids never shows it.
        return self.env["stock.valuation.layer"].search(
            [("product_id", "=", self.product.id)], order="id"
        )

    def test_net_cost_survives_the_vendor_bill(self):
        order, move = self._receive()
        value_on_receipt = sum(self._product_layers().mapped("value"))
        self.assertAlmostEqual(value_on_receipt, move.cost_unit, places=2)
        self.assertGreater(move.icms_value, 0)
        # The layer is net, so it differs from what the bill will charge.
        self.assertLess(value_on_receipt, move.price_unit)

        invoice = self._bill(order)
        invoice_line = invoice.invoice_line_ids[0]
        # Every condition for a price difference is met.
        self.assertTrue(invoice_line.purchase_line_id)
        self.assertNotEqual(invoice_line.product_id.cost_method, "standard")
        self.assertGreater(invoice_line.price_subtotal, value_on_receipt)

        invoice.action_post()

        self.assertEqual(
            self._product_layers().mapped("value"),
            [value_on_receipt],
            "the vendor bill must not add a correction layer",
        )

    def test_price_difference_is_net_of_recoverable_taxes(self):
        """A bill above the order price corrects only the net difference."""
        order, move = self._receive()
        receipt_layer = self._product_layers()
        self.assertEqual(len(receipt_layer), 1)

        invoice = self._bill(order)
        invoice_line = invoice.invoice_line_ids[0]
        invoice_line.price_unit = move.price_unit + 50.0
        self.assertAlmostEqual(
            invoice_line.price_subtotal, move.price_unit + 50.0, places=2
        )

        invoice.action_post()

        layers = self._product_layers()
        self.assertEqual(len(layers), 2, layers.mapped("value"))
        correction = layers - receipt_layer
        self.assertEqual(correction.stock_valuation_layer_id, receipt_layer)
        # The 50.00 carry their own recoverable taxes: on 800.00 with 96.00 of
        # ICMS the net cost keeps 704.00 / 800.00, so 44.00 reach the stock,
        # not the 50.00 and certainly not 96.00 + 50.00.
        net_difference = 50.0 * move.cost_unit / move.price_unit
        self.assertAlmostEqual(correction.value, net_difference, places=2)
        self.assertAlmostEqual(
            sum(layers.mapped("value")),
            move.cost_unit + net_difference,
            places=2,
        )

    def test_net_cost_visible_on_the_purchase_order_line(self):
        """The buyer sees the net cost before approving the order."""
        order = self._make_order()
        line = order.order_line[0]

        self.assertGreater(line.icms_value, 0)
        self.assertAlmostEqual(line.cost_unit, line.price_unit - line.icms_value, 2)
        self.assertLess(line.cost_unit, line.price_unit)
        self.assertEqual(line.creditability_origin, "derived")

    def test_net_cost_per_unit_on_a_multi_quantity_line(self):
        """The cost is per unit, so it divides by the ordered quantity."""
        order = self._make_order(qty=4.0)
        line = order.order_line[0]

        self.assertAlmostEqual(
            line.cost_unit, line.price_unit - line.icms_value / 4.0, 2
        )
