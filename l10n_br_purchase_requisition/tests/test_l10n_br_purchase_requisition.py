# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.purchase_requisition.tests.common import TestPurchaseRequisitionCommon


class L10nBrPurchaseRequisition(TestPurchaseRequisitionCommon):
    def test_l10n_br_purchase_requisition(self):

        # Create purchase order from purchase requisition
        po_form = Form(
            self.env["purchase.order"].with_context(
                default_requisition_id=self.requisition1.id
            )
        )
        po_form.partner_id = self.res_partner_1
        po = po_form.save()

        self.assertTrue(po.fiscal_operation_id)
        self.assertTrue(po.order_line.fiscal_operation_id)
        self.assertTrue(po.order_line.fiscal_operation_line_id)
        self.assertTrue(po.order_line.fiscal_tax_ids)
