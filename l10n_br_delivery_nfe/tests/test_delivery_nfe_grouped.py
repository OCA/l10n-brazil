# Copyright (C) 2024 Diego Paradeda - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.addons.l10n_br_stock_account.tests.common import TestBrPickingInvoicingCommon


class TestDeliveryNFe(TestBrPickingInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    # Test Grouped Picking
    def test_invoicing_picking_volume_grouped_by_partner(self):
        """Test Invoicing Picking NFe volume - Grouped by partner"""
        self.invoice_model = self.env["account.move"]
        self.invoice_wizard = self.env["stock.invoice.onshipping"]
        self.prod1 = self.env.ref("product.product_product_12")
        self.prod2 = self.env.ref("product.product_product_16")
        self._change_user_company(self.env.ref("l10n_br_base.empresa_lucro_presumido"))
        picking1 = self.env.ref("l10n_br_stock_account.lucro_presumido-picking_1")
        picking2 = self.env.ref("l10n_br_stock_account.lucro_presumido-picking_2")
        self.brand_id1 = self.env["product.brand"].create({"name": "marca teste"})
        self.brand_id2 = self.env["product.brand"].create({"name": "marca2 teste"})

        # Ensure pickings have the same partner_id. This is a basic requirement
        self.assertEqual(
            picking1.partner_id,
            picking2.partner_id,
            "Partner must be the same for both pickings. This is a test "
            "requirement.",
        )

        # Set product volume data
        self.prod1.product_volume_type = "esp1 teste"
        self.prod1.product_brand_id = self.brand_id1
        self.prod2.product_volume_type = "esp2 teste"
        self.prod2.product_brand_id = self.brand_id2
        self.prod1.weight = 1
        self.prod2.weight = 3
        self.prod1.net_weight = 1
        self.prod2.net_weight = 5

        # Validate: Picking 1
        picking1.set_to_be_invoiced()
        self.picking_move_state(picking1)
        self.assertEqual(picking1.state, "done")

        # Validate: Picking 2
        picking2.set_to_be_invoiced()
        self.picking_move_state(picking2)
        self.assertEqual(picking2.state, "done")

        # Invoice
        wizard_obj = self.invoice_wizard.with_context(
            active_ids=[picking1.id, picking2.id],
            active_model=picking1._name,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.group = "partner"
        wizard.onchange_group()
        wizard.fiscal_operation_journal = False
        wizard.action_generate()
        self.assertEqual(picking1.invoice_state, "invoiced")
        self.assertEqual(picking2.invoice_state, "invoiced")

        # Fiscal details
        p1_doc_id = picking1.invoice_ids.fiscal_document_id
        p2_doc_id = picking2.invoice_ids.fiscal_document_id
        p1_volume_ids = p1_doc_id.nfe40_vol
        p2_volume_ids = p2_doc_id.nfe40_vol

        self.assertEqual(
            p1_volume_ids.mapped("nfe40_qVol"),
            ["4", "4"],
            "Unexpected value for the field nfe40_qVol in Fiscal Details.",
        )
        self.assertEqual(p1_volume_ids, p2_volume_ids)
