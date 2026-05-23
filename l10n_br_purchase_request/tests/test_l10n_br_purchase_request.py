# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID
from odoo.tests import TransactionCase


class L10nBrPurchaseRequestBaseTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")

        cls.purchase_request_obj = cls.env["purchase.request"]
        cls.purchase_request_line_obj = cls.env["purchase.request.line"]
        vals = {
            "company_id": cls.company.id,
            "requested_by": SUPERUSER_ID,
        }
        cls.purchase_request = cls.purchase_request_obj.create(vals)
        vals = {
            "request_id": cls.purchase_request.id,
            "product_id": cls.env.ref("product.product_product_12").id,
            "product_uom_id": cls.env.ref("uom.product_uom_unit").id,
            "product_qty": 5.0,
        }
        cls.purchase_request_line_obj.create(vals)
        cls.supplier = cls.env.ref("l10n_br_base.res_partner_dell")
        cls.wiz = cls.env["purchase.request.line.make.purchase.order"]

    def test_purchase_request_to_rfq(self):
        request = self.purchase_request
        self.assertTrue(request.to_approve_allowed)

        request.button_approved()
        vals = {
            "supplier_id": self.supplier.id,
        }
        wiz_id = self.wiz.with_context(
            active_model="purchase.request.line", active_ids=[request.line_ids[0].id]
        ).create(vals)
        wiz_id.with_context(default_company_id=self.company.id).make_purchase_order()
        purchase_order = request.line_ids[0].purchase_lines[0].order_id
        self.assertEqual(purchase_order.ind_final, "0")
        self.assertTrue(purchase_order)
        self.assertTrue(purchase_order.order_line.fiscal_operation_line_id)
        self.assertTrue(purchase_order.order_line.fiscal_tax_ids)
        self.assertTrue(purchase_order.order_line.taxes_id)

    def test_purchase_request_to_rfq_ind_final(self):
        request = self.purchase_request
        self.assertTrue(request.to_approve_allowed)

        request.button_approved()
        self.supplier.ind_final = "1"
        vals = {
            "supplier_id": self.supplier.id,
        }
        wiz_id = self.wiz.with_context(
            active_model="purchase.request.line", active_ids=[request.line_ids[0].id]
        ).create(vals)
        wiz_id.with_context(default_company_id=self.company.id).make_purchase_order()
        purchase_order = request.line_ids[0].purchase_lines[0].order_id
        self.assertEqual(purchase_order.ind_final, "1")
