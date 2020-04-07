# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common
from odoo.tests.common import Form


class TestL10nBRPurchase(common.TransactionCase):
    def setUp(self):
        super(TestL10nBRPurchase, self).setUp()
        self.purchase_order_1 = self.env.ref(
            "l10n_br_purchase.l10n_br_purchase_order-demo_1")
        self.invoice_model = self.env["account.invoice"]

    def test_l10n_br_purchase_order(self):
        """
        Test Purchase Order in Brazilian Localization.
        """

        self.purchase_order_1.onchange_partner_id()

        self.assertTrue(
            self.purchase_order_1.operation_id,
            "Error to inform Operation in Purchase Order.",
        )

        for line in self.purchase_order_1.order_line:
            line._onchange_product_id()
            line._onchange_operation_id()
            line._onchange_operation_line_id()
            line._onchange_fiscal_taxes()
            self.assertTrue(
                line.operation_line_id,
                "Error to mapping Operation Line in Purchase Order Line.",
            )

        self.purchase_order_1.button_confirm()

        self.assertEquals(
            self.purchase_order_1.state, "purchase",
            "Error to confirm Purchase Order."
        )

        self.assertTrue(
            self.purchase_order_1.picking_ids,
            "Purchase Order: no picking created for"
            ' "invoice on delivery" stockable products',
        )

        res = self.purchase_order_1.with_context(
            create_bill=True).action_view_invoice()
        ctx = res.get('context')
        f = Form(self.invoice_model.with_context(ctx),
                 view='account.invoice_supplier_form')
        invoice = f.save()

        self.assertTrue(
            self.purchase_order_1.invoice_ids,
            "Purchase Order: no invoice created."
        )
        self.assertTrue(
            invoice.operation_id,
            "Invoice: created without field Operation."
        )
        self.assertTrue(
            invoice.purchase_id,
            "Invoice: created without field Purchase."
        )
        for line in invoice.invoice_line_ids:
            self.assertTrue(
                line.operation_line_id,
                "Invoice Line: created without field Operation Line."
            )
