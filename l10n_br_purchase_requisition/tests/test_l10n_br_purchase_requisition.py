# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.purchase_requisition.tests.common import TestPurchaseRequisitionCommon


class L10nBrPurchaseRequisition(TestPurchaseRequisitionCommon):
    def test_01_requisition_lines_get_fiscal_info(self):
        requisition = self.env["purchase.requisition"].create(
            {
                "vendor_id": self.res_partner_1.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_09.id,
                            "product_qty": 10,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

        po_form = Form(self.env["purchase.order"])
        po_form.partner_id = self.res_partner_1
        po_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_compras")
        po_form.requisition_id = requisition
        self.assertEqual(
            po_form.fiscal_operation_id,
            self.env.ref("l10n_br_fiscal.fo_compras"),
        )

        po = po_form.save()
        self.assertTrue(len(po.order_line) > 0)

        self.assertEqual(
            po.order_line[0].fiscal_operation_id,
            self.env.ref("l10n_br_fiscal.fo_compras"),
        )

        partner_2 = self.env["res.partner"].create({"name": "Partner 2"})

        po_memory = self.env["purchase.order"].new(
            {
                "partner_id": self.res_partner_1.id,
                "requisition_id": requisition.id,
                "company_id": self.env.company.id,
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_compras").id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_09.id,
                            "product_qty": 10,
                            "price_unit": 100,
                            "fiscal_operation_id": False,
                        },
                    )
                ],
            }
        )

        po_memory.partner_id = partner_2.id
        po_memory.onchange_partner_id()

        self.assertEqual(
            po_memory.fiscal_operation_id, self.env.ref("l10n_br_fiscal.fo_compras")
        )
        self.assertEqual(
            po_memory.order_line[0].fiscal_operation_id,
            self.env.ref("l10n_br_fiscal.fo_compras"),
        )
