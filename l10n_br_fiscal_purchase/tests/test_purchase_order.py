#  Copyright 2023 Felipe Zago Rodrigues - KMEE
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


class TestPurchaseOrder(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner_1 = self.env["res.partner"].create({"name": "PARTNER TEST 1"})
        self.product_1 = self.env["product.product"].create(
            {
                "name": "PRODUCT TEST 1",
                "list_price": 10,
                "uom_id": self.env.ref("uom.product_uom_unit").id,
            }
        )
        self.nfe_fiscal_document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                "fiscal_operation_type": "out",
                "fiscal_line_ids": [
                    (0, 0, {"name": "LINE TEST 1", "product_id": self.product_1.id})
                ],
                "active": False,
            }
        )

    def create_and_invoice_purchase_order(self):
        purchase_order = (
            self.env["purchase.order"]
            .with_context(tracking_disable=True)
            .create(
                {
                    "partner_id": self.partner_1.id,
                    "origin_document_id": self.nfe_fiscal_document.id,
                }
            )
        )
        PurchaseOrderLine = self.env["purchase.order.line"].with_context(
            tracking_disable=True
        )
        PurchaseOrderLine.create(
            {
                "name": self.product_1.name,
                "product_id": self.product_1.id,
                "product_qty": 10.0,
                "product_uom": self.product_1.uom_id.id,
                "price_unit": self.product_1.list_price,
                "order_id": purchase_order.id,
                "origin_document_line_id": self.nfe_fiscal_document.fiscal_line_ids[
                    0
                ].id,
            }
        )
        purchase_order.confirm_and_create_invoice()
        return purchase_order

    def test_create_and_invoice_purchase(self):
        purchase_order_1 = self.create_and_invoice_purchase_order()
        purchase_order_2 = self.create_and_invoice_purchase_order()

        prepare_vals = purchase_order_1._prepare_invoice()
        self.assertEqual(
            prepare_vals["fiscal_document_id"], self.nfe_fiscal_document.id
        )
        self.assertEqual(
            prepare_vals["document_type_id"],
            self.nfe_fiscal_document.document_type_id.id,
        )

        self.nfe_fiscal_document.linked_purchase_ids = [(4, purchase_order_1.id)]
        action = self.nfe_fiscal_document.action_open_purchase()
        self.assertEqual(action["res_id"], purchase_order_1.id)

        self.nfe_fiscal_document.linked_purchase_ids = [(4, purchase_order_2.id)]
        action = self.nfe_fiscal_document.action_open_purchase()
        self.assertIn("domain", action)

        self.assertEqual(self.nfe_fiscal_document.linked_purchase_count, 2)
