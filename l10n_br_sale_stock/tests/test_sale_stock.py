# Copyright 2020 KMEE
# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.l10n_br_sale.hooks import sale_set_journal_in_fiscal_operation
from odoo.addons.l10n_br_stock_account.tests.common import TestBrPickingInvoicingCommon


@tagged("post_install", "-at_install")
class TestSaleStock(TestBrPickingInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Set sale invoicing policy to stock_picking for all companies
        cls.companies = cls.env["res.company"].search(
            [("sale_invoicing_policy", "=", "sale_order")]
        )
        for company in cls.companies:
            company.sale_invoicing_policy = "stock_picking"

        sale_set_journal_in_fiscal_operation(cls.cr)

        # Create test records that would normally come from demo data
        cls._setup_test_sale_orders()

    @classmethod
    def _setup_test_sale_orders(cls):
        """Create test sale orders in Python to avoid FK issues with demo XML."""
        partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        partner_addr_ak2 = cls.env.ref("l10n_br_base.res_partner_address_ak2")
        partner_addr_ak3 = cls.env.ref("l10n_br_base.res_partner_address_ak3")
        fo_venda = cls.env.ref("l10n_br_fiscal.fo_venda")
        pricelist = cls.env.ref("sale_stock_picking_invoicing.demo_pricelist")
        product_prod = cls.env.ref("product.product_delivery_01")
        product_serv = cls.env.ref("product.product_product_12")
        team = cls.env.ref("sales_team.crm_team_1", raise_if_not_found=False)
        user_admin = cls.env.ref("base.user_admin")

        cls._sale_1_vals = {
            "partner_id": partner.id,
            "partner_invoice_id": partner.id,
            "partner_shipping_id": partner_addr_ak2.id,
            "fiscal_operation_id": fo_venda.id,
            "pricelist_id": pricelist.id,
            "user_id": user_admin.id,
        }
        cls._sale_2_vals = {
            "partner_id": partner.id,
            "partner_invoice_id": partner_addr_ak3.id,
            "partner_shipping_id": partner.id,
            "fiscal_operation_id": fo_venda.id,
            "pricelist_id": pricelist.id,
            "user_id": user_admin.id,
        }
        cls._sale_3_vals = {
            "partner_id": partner.id,
            "partner_invoice_id": partner.id,
            "partner_shipping_id": partner.id,
            "fiscal_operation_id": fo_venda.id,
            "pricelist_id": pricelist.id,
            "user_id": user_admin.id,
        }
        cls._sale_4_vals = {
            "partner_id": partner.id,
            "partner_invoice_id": partner.id,
            "partner_shipping_id": partner_addr_ak3.id,
            "fiscal_operation_id": fo_venda.id,
            "pricelist_id": pricelist.id,
            "user_id": user_admin.id,
        }

        if team:
            for val in [
                cls._sale_1_vals,
                cls._sale_2_vals,
                cls._sale_3_vals,
                cls._sale_4_vals,
            ]:
                val["team_id"] = team.id

        cls.product_prod = product_prod
        cls.product_serv = product_serv
        cls.fo_venda = fo_venda
        cls.partner = partner
        cls.partner_addr_ak2 = partner_addr_ak2
        cls.partner_addr_ak3 = partner_addr_ak3
        cls.pricelist = pricelist

    def _create_sale_order(self, vals, lines):
        """Helper to create a sale order with lines."""
        so = self.env["sale.order"].create(vals)
        for line_vals in lines:
            line_vals["order_id"] = so.id
            self.env["sale.order.line"].create(line_vals)
        return so

    def test_02_sale_stock_return(self):
        """
        Test a SO with a product invoiced on delivery. Deliver and invoice
        the SO, then do a return of the picking. Check that a refund
        invoice is well generated.
        """
        self.product = self.env.ref("product.product_delivery_01")

        so_vals = {
            "partner_id": self.partner_addr_ak2.id,
            "partner_invoice_id": self.partner_addr_ak2.id,
            "partner_shipping_id": self.partner_addr_ak2.id,
            "pricelist_id": self.pricelist.id,
            "fiscal_operation_id": self.fo_venda.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "name": self.product.name,
                        "product_id": self.product.id,
                        "product_uom_qty": 3.0,
                        "product_uom": self.product.uom_id.id,
                        "price_unit": self.product.list_price,
                        "fiscal_operation_id": self.fo_venda.id,
                    },
                )
            ],
        }
        self.so = self.env["sale.order"].create(so_vals)

        self.so.action_confirm()
        self.assertTrue(
            self.so.picking_ids,
            'Sale Stock: no picking created for "invoice on '
            'delivery" storable products',
        )
        self.assertTrue(
            len(self.so.picking_ids) == 1,
            "More than one stock picking for sale.order",
        )
        self.so.picking_ids.set_to_be_invoiced()

    def test_compatible_with_international_case(self):
        """
        Test compatibility with international cases or
        without Fiscal Operation.
        """
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

    def test_synchronize_sale_partner_shipping_in_stock_picking(self):
        """
        Test the synchronize Sale Partner Shipping in Stock Picking
        """
        so = self._create_sale_order(
            self._sale_1_vals,
            [
                {
                    "product_id": self.product_prod.id,
                    "product_uom_qty": 2,
                    "name": self.product_prod.name,
                    "price_unit": 100.0,
                    "fiscal_operation_id": self.fo_venda.id,
                },
            ],
        )
        so.action_confirm()
        picking = so.picking_ids
        so.partner_shipping_id = self.partner_addr_ak2.id
        self.assertEqual(so.partner_shipping_id, picking.partner_id)
