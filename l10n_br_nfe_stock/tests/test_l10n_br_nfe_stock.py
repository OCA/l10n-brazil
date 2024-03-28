# @ 2023 KMEE - www.kmee.com.br -
# Renan Hiroki Bastos <renan.hiroki@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.l10n_br_purchase.tests import test_l10n_br_purchase


class L10nBrNfeStockPurchase(test_l10n_br_purchase.L10nBrPurchaseBaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product_1 = cls.env["product.product"].create(
            {
                "name": "PRODUCT TEST 1",
                "list_price": 10,
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
            }
        )
        cls.nfe_fiscal_document = cls.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": cls.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                "fiscal_operation_type": "out",
                "fiscal_line_ids": [
                    (0, 0, {"name": "LINE TEST 1", "product_id": cls.product_1.id})
                ],
            }
        )
        cls.picking_no_product = cls.env["stock.picking"].create(
            {
                "partner_id": cls.env.ref("l10n_br_base.lucro_presumido_partner").id,
                "picking_type_id": cls.env.ref("stock.picking_type_in").id,
                "location_dest_id": cls.env.ref(
                    "stock.picking_type_in"
                ).default_location_dest_id.id,
                "location_id": cls.env.ref("stock.stock_location_suppliers").id,
            }
        )

    def test_l10n_br_nfe_stock_prepare_invoice(self):
        self._change_user_company(self.company)
        self._run_purchase_order_onchanges(self.po_products)
        self.po_products.origin_document_id = self.nfe_fiscal_document.id

        self.po_products.with_context(tracking_disable=True).button_confirm()

        invoice_values = {
            "partner_id": self.po_products.partner_id.id,
            "move_type": "in_invoice",
        }

        invoice_values.update(self.po_products._prepare_br_fiscal_dict())

        invoice_values.update(self.po_products._prepare_invoice())
        self.assertEqual(
            invoice_values["document_type_id"],
            self.nfe_fiscal_document.document_type_id.id,
        )

    def test_l10n_br_nfe_stock_actions(self):
        # Test open purchase actions
        self.nfe_fiscal_document.linked_purchase_ids = [(4, self.po_products.id)]
        action = self.nfe_fiscal_document.action_open_purchase()
        self.assertEqual(action["res_id"], self.po_products.id)

        self.nfe_fiscal_document.linked_purchase_ids = [(4, self.po_products.copy().id)]
        action = self.nfe_fiscal_document.action_open_purchase()
        self.assertIn("domain", action)

        self.assertEqual(self.nfe_fiscal_document.linked_purchase_count, 2)

        # Test open picking actions
        self.nfe_fiscal_document.linked_picking_ids = [(4, self.picking_no_product.id)]
        action = self.nfe_fiscal_document.action_open_picking()
        self.assertEqual(action["res_id"], self.picking_no_product.id)

        self.nfe_fiscal_document.linked_picking_ids = [
            (4, self.picking_no_product.copy().id)
        ]
        action = self.nfe_fiscal_document.action_open_picking()
        self.assertIn("domain", action)

        self.assertEqual(self.nfe_fiscal_document.linked_picking_count, 2)

        # Test open document actions
        action = self.po_products.action_open_document()
        self.assertEqual(action["res_id"], self.nfe_fiscal_document.id)

        self.po_products.linked_document_ids = [(4, self.nfe_fiscal_document.copy().id)]
        action = self.po_products.action_open_document()
        self.assertIn("domain", action)

        self.assertEqual(self.po_products.linked_document_count, 2)

        action = self.picking_no_product.action_open_document()
        self.assertEqual(action["res_id"], self.nfe_fiscal_document.id)

        self.picking_no_product.linked_document_ids = [
            (4, self.nfe_fiscal_document.copy().id)
        ]
        action = self.picking_no_product.action_open_document()
        self.assertIn("domain", action)

        self.assertEqual(self.picking_no_product.linked_document_count, 2)
