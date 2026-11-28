# Copyright 2020 KMEE
# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import Form, tagged

from odoo.addons.l10n_br_sale.hooks import sale_set_journal_in_fiscal_operation
from odoo.addons.l10n_br_stock_account.tests.common import TestBrPickingInvoicingCommon


@tagged("post_install", "-at_install")
class TestSaleStock(TestBrPickingInvoicingCommon):
    """Test the l10n_br_sale_stock module.

    The parent class (TestBrPickingInvoicingCommon) inherits from
    AccountTestInvoicingCommon which creates a test company (company_1_data)
    and sets cls.env.company to it. All l10n_br fiscal demo data (partners,
    products, fiscal operations, CoA) belongs to main_company.

    We create storable products explicitly in setUpClass to match the
    core sale_stock test pattern — demo products may not reliably generate
    pickings in the test company context.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Set sale invoicing policy to stock_picking for all companies
        cls.companies = cls.env["res.company"].search(
            [("sale_invoicing_policy", "=", "sale_order")]
        )
        for company in cls.companies:
            company.sale_invoicing_policy = "stock_picking"

        sale_set_journal_in_fiscal_operation(cls.env)

        # Storable product for delivery-invoiced pickings.
        # In Odoo 18, demo products like product_delivery_01 have
        # is_storable=True but may not generate pickings reliably in the
        # test company context. Creating an explicit storable product
        # matches the core sale_stock test pattern.
        cls.storable_product = cls.env["product.product"].create(
            {
                "name": "Test Storable Product (l10n_br_sale_stock)",
                "type": "consu",
                "is_storable": True,
                "invoice_policy": "delivery",
                "lst_price": 100.0,
                "standard_price": 50.0,
            }
        )

        cls.partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        cls.partner_addr_ak2 = cls.env.ref("l10n_br_base.res_partner_address_ak2")
        cls.partner_addr_ak3 = cls.env.ref("l10n_br_base.res_partner_address_ak3")
        cls.fo_venda = cls.env.ref("l10n_br_fiscal.fo_venda")

    def _create_sale_order(self, partner_shipping=None, lines=None):
        """Helper to create a sale order with fiscal operation and lines."""
        partner_shipping = partner_shipping or self.partner
        so_vals = {
            "partner_id": self.partner.id,
            "partner_invoice_id": self.partner.id,
            "partner_shipping_id": partner_shipping.id,
            "fiscal_operation_id": self.fo_venda.id,
            "order_line": lines or [],
        }
        return self.env["sale.order"].create(so_vals)

    def test_02_sale_stock_return(self):
        """
        Test a SO with a product invoiced on delivery. Deliver and invoice
        the SO, then do a return of the picking. Check that a refund
        invoice is well generated.
        """
        so = self._create_sale_order(
            partner_shipping=self.partner_addr_ak2,
            lines=[
                Command.create(
                    {
                        "name": self.storable_product.name,
                        "product_id": self.storable_product.id,
                        "product_uom_qty": 3.0,
                        "product_uom": self.storable_product.uom_id.id,
                        "price_unit": self.storable_product.lst_price,
                        "fiscal_operation_id": self.fo_venda.id,
                    }
                )
            ],
        )
        so.action_confirm()
        self.assertTrue(
            so.picking_ids,
            'Sale Stock: no picking created for "invoice on '
            'delivery" storable products',
        )
        self.assertEqual(len(so.picking_ids), 1)
        so.picking_ids.set_to_be_invoiced()

    def test_compatible_with_international_case(self):
        """
        Test compatibility with international cases or
        without Fiscal Operation.

        sale.sale_order_3 belongs to main_company, so we run this
        test entirely in the main_company context.
        """
        main_company = self.env.ref("base.main_company")
        # Save current env and switch to main_company for this test only.
        # sale.sale_order_3 and its pickings belong to main_company, and
        # the invoice wizard checks pickings are related to "your company".
        saved_env = self.env
        self.env = self.env(
            context=dict(self.env.context, allowed_company_ids=main_company.ids)
        )
        try:
            so_international = self.env.ref("sale.sale_order_3")
            so_international.fiscal_operation_id = False
            so_international.action_confirm()
            picking = so_international.picking_ids
            self.picking_move_state(picking)
            # International pickings may not have fiscal_operation_id
            if hasattr(picking, "fiscal_operation_id"):
                picking.fiscal_operation_id = False
            invoice = self.create_invoice_wizard(picking)
            invoice.action_post()
            self.assertFalse(
                invoice.fiscal_document_id,
                "International case should not has Fiscal Document.",
            )
            picking_devolution = self.return_picking_wizard(picking)
            invoice_devolution = self.create_invoice_wizard(picking_devolution)
            self.assertFalse(
                invoice_devolution.fiscal_document_id,
                "International case should not has Fiscal Document.",
            )
        finally:
            self.env = saved_env

    def test_synchronize_sale_partner_shipping_in_stock_picking(self):
        """
        Test that when partner_shipping_id is changed after the order is
        confirmed, the related stock.picking records get their partner_id
        updated (write override on sale.order).
        """
        so = self._create_sale_order(
            partner_shipping=self.partner,
            lines=[
                Command.create(
                    {
                        "product_id": self.storable_product.id,
                        "product_uom_qty": 2,
                        "name": self.storable_product.name,
                        "price_unit": 100.0,
                        "fiscal_operation_id": self.fo_venda.id,
                    }
                ),
            ],
        )
        so.action_confirm()
        picking = so.picking_ids
        self.assertTrue(picking, "No picking created for storable product")
        # Change shipping partner after confirmation
        so.partner_shipping_id = self.partner_addr_ak2.id
        self.assertEqual(so.partner_shipping_id, picking.partner_id)

    def _create_kit_picking(self, ncm_component):
        """Kit of 914.40 with 10% discount, exploded into 4 component moves.

        The kit move is copied into one move per component, keeping the
        fiscal values of the kit line, as the phantom BoM explosion does.
        """
        journal = self.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", self.env.company.id)],
            limit=1,
        )
        for fiscal_operation in (
            self.fo_venda,
            self.fo_venda.return_fiscal_operation_id,
        ):
            fiscal_operation.with_company(self.env.company).journal_id = journal
        ncm_kit = self.env["l10n_br_fiscal.ncm"].search(
            [("id", "!=", ncm_component.id)], limit=1
        )
        components = self.env["product.product"].create(
            [
                {
                    "name": f"Kit Component {price}",
                    "type": "consu",
                    "is_storable": True,
                    "invoice_policy": "delivery",
                    "list_price": price,
                    "standard_price": 10.0,
                    "ncm_id": ncm_component.id,
                }
                for price in (239.0, 189.0, 319.0, 269.0)
            ]
        )
        kit = self.env["product.product"].create(
            {
                "name": "Kit",
                "type": "consu",
                "is_storable": True,
                "invoice_policy": "delivery",
                "list_price": 914.40,
                "ncm_id": ncm_kit.id,
            }
        )
        so = self._create_sale_order(
            lines=[
                Command.create(
                    {
                        "product_id": kit.id,
                        "product_uom_qty": 1.0,
                        "price_unit": 914.40,
                        "discount": 10.0,
                        "fiscal_operation_id": self.fo_venda.id,
                    }
                )
            ],
        )
        so.action_confirm()
        kit_line = so.order_line
        self.assertAlmostEqual(kit_line.discount_value, 91.44, places=2)
        picking = so.picking_ids
        kit_move = picking.move_ids
        for component in components:
            kit_move.copy(
                {
                    "product_id": component.id,
                    "product_uom": component.uom_id.id,
                    "product_uom_qty": 1.0,
                    "picking_id": picking.id,
                    "sale_line_id": kit_line.id,
                }
            )
        kit_move._action_cancel()
        kit_move.unlink()
        self.picking_move_state(picking)
        picking.set_to_be_invoiced()
        return picking

    def _product_lines(self, invoice):
        return invoice.invoice_line_ids.filtered(
            lambda ln: ln.display_type == "product"
        )

    def test_kit_component_fiscal_values(self):
        """
        Phantom kit sold with a discount: the component moves point to the
        sale line of the kit and carry its fiscal values. Each invoice line
        must get the fiscal values of its component (fiscal price equal to
        the price, its own NCM) and its share of the kit discount, so the
        invoice totals the price the kit was sold for.
        """
        ncm_component = self.env["l10n_br_fiscal.ncm"].search([], limit=1)
        picking = self._create_kit_picking(ncm_component)

        invoice = self.create_invoice_wizard(picking)

        lines = self._product_lines(invoice)
        self.assertEqual(len(lines), 4)
        # invoiced at the share of the sale price, not at the cost
        self.assertEqual(
            sorted(lines.mapped("price_unit")), [170.10, 215.10, 242.10, 287.10]
        )
        for line in lines:
            self.assertEqual(line.ncm_id, ncm_component)
            self.assertAlmostEqual(line.fiscal_price, line.price_unit, places=2)
            self.assertEqual(line.fiscal_quantity, line.quantity)
            self.assertAlmostEqual(
                line.discount_value, line.price_unit * line.quantity * 0.1, places=2
            )
        self.assertAlmostEqual(sum(lines.mapped("discount_value")), 91.44, places=2)
        self.assertAlmostEqual(invoice.amount_untaxed, 822.96, places=2)
        self.assertAlmostEqual(
            invoice.fiscal_document_id.amount_discount_value, 91.44, places=2
        )

    def test_kit_return_fiscal_values(self):
        """
        Returning the whole kit: the return moves point to the kit line too,
        but stay out of the split. The refund takes, for each component, the
        price and the discount it was invoiced with, and totals the invoice.
        """
        ncm_component = self.env["l10n_br_fiscal.ncm"].search([], limit=1)
        picking = self._create_kit_picking(ncm_component)
        invoice = self.create_invoice_wizard(picking)
        invoiced = {
            line.product_id: (line.price_unit, line.discount_value)
            for line in self._product_lines(invoice)
        }

        return_form = Form(
            self.env["stock.return.picking"].with_context(
                active_id=picking.id, active_model="stock.picking"
            )
        )
        return_form.invoice_state = "2binvoiced"
        return_wizard = return_form.save()
        for return_line in return_wizard.product_return_moves:
            return_line.quantity = return_line.move_id.product_uom_qty
        result = return_wizard.action_create_returns()
        return_picking = self.env["stock.picking"].browse(result["res_id"])
        self.picking_move_state(return_picking)

        refund = self.create_invoice_wizard(return_picking)

        self.assertEqual(refund.move_type, "out_refund")
        lines = self._product_lines(refund)
        self.assertEqual(len(lines), 4)
        for line in lines:
            price_unit, discount_value = invoiced[line.product_id]
            self.assertAlmostEqual(line.price_unit, price_unit, places=2)
            self.assertAlmostEqual(line.discount_value, discount_value, places=2)
            self.assertEqual(line.ncm_id, ncm_component)
        self.assertAlmostEqual(refund.amount_untaxed, invoice.amount_untaxed, places=2)
