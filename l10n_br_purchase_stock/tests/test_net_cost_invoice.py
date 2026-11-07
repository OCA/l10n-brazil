# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import TransactionCase


class TestNetCostSurvivesInvoice(TransactionCase):
    """The net cost must survive the vendor bill.

    The full purchase path is order, receipt, bill. On posting a vendor
    bill, ``purchase_stock`` compares the gross price of the invoice line
    against the cost the valuation layer holds and, when they differ, writes
    a correction layer that pushes the difference back into stock.

    That difference is exactly the recoverable tax this module took out, so
    a correction would silently undo the net cost on the very path every
    customer uses. It does not happen today, and this test is what keeps it
    that way: it fails the moment a change in the core or in another module
    starts reverting the layer.
    """

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

        # A product of its own: switching a category to real time revalues
        # whatever is already in stock, so a demo product would drag the
        # fixture into the test.
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

    def test_net_cost_survives_the_vendor_bill(self):
        order = (
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
                                "product_qty": 1.0,
                                "price_unit": 800.0,
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
        order.button_confirm()

        picking = order.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for line in picking.move_ids.move_line_ids:
            line.qty_done = line.reserved_uom_qty
        picking.with_context(skip_immediate=True, skip_backorder=True).button_validate()

        move = picking.move_ids[0]
        value_on_receipt = sum(move.stock_valuation_layer_ids.mapped("value"))
        self.assertAlmostEqual(value_on_receipt, move.cost_unit, places=2)
        self.assertGreater(move.icms_value, 0)
        # The layer is net, so it differs from what the bill will charge.
        self.assertLess(value_on_receipt, move.price_unit)

        invoice = self.env["account.move"].browse(
            order.action_create_invoice()["res_id"]
        )
        invoice.invoice_date = fields.Date.today()
        invoice_line = invoice.invoice_line_ids[0]
        # The conditions that would trigger a price difference are all met:
        # the line is tied to the order, the product is not standard costed
        # and the gross amount differs from the layer.
        self.assertTrue(invoice_line.purchase_line_id)
        self.assertNotEqual(invoice_line.product_id.cost_method, "standard")
        self.assertGreater(invoice_line.price_subtotal, value_on_receipt)

        invoice.action_post()

        layers = move.stock_valuation_layer_ids
        self.assertEqual(
            len(layers), 1, "the vendor bill must not add a correction layer"
        )
        self.assertAlmostEqual(sum(layers.mapped("value")), value_on_receipt, places=2)
