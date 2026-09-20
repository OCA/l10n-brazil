# Copyright (C) 2026 - Madooit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


@tagged("post_install", "-at_install", "test_update_po_from_nfe")
class TestUpdatePOFromNfe(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.fiscal_operation_line = cls.env.ref(
            "l10n_br_fiscal.fo_compras_compras_comercializacao"
        )
        cls.po = cls._create_po()
        cls.bill = cls._create_bill()

    @classmethod
    def _create_po(cls):
        order_form = Form(cls.env["purchase.order"])
        order_form.partner_id = cls.partner_a
        order_form.fiscal_operation_id = cls.fiscal_operation
        with order_form.order_line.new() as line:
            line.product_id = cls.product_a
            line.product_qty = 10.0
            line.price_unit = 100.0
            line.fiscal_operation_line_id = cls.fiscal_operation_line
        order = order_form.save()
        line = order.order_line[0]
        line.partner_order = "PO-REF-1"
        line.partner_order_line = "1"
        return order

    @classmethod
    def _create_bill(cls):
        bill = cls.init_invoice(
            "in_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=cls.fiscal_operation,
            fiscal_operation_lines=[cls.fiscal_operation_line],
            document_serie="1",
            document_number="42",
        )
        fiscal_line = bill.fiscal_document_id.fiscal_line_ids.filtered(
            lambda fline: fline.product_id == cls.product_a
        )
        fiscal_line.partner_order = "PO-REF-1"
        fiscal_line.partner_order_line = "1"
        return bill

    def _open_wizard(self):
        action = self.bill.action_update_po_from_nfe()
        return self.env["purchase.update.from.nfe.wizard"].browse(action["res_id"])

    def test_find_purchase_by_nfe_reference(self):
        wizard_model = self.env["purchase.update.from.nfe.wizard"]
        self.assertEqual(self.bill.invoice_line_ids.partner_order, "PO-REF-1")
        self.assertEqual(wizard_model._find_purchase(self.bill), self.po)

    def test_wizard_defaults(self):
        wizard = self._open_wizard()
        self.assertEqual(wizard.purchase_id, self.po)
        self.assertEqual(len(wizard.line_ids), 1)
        line = wizard.line_ids[0]
        self.assertEqual(line.partner_order, "PO-REF-1")
        self.assertEqual(line.partner_order_line, "1")
        self.assertEqual(line.new_quantity, self.bill.invoice_line_ids.quantity)
        self.assertEqual(line.new_price_unit, self.bill.invoice_line_ids.price_unit)

    def test_apply_updates_po(self):
        wizard = self._open_wizard()
        line = wizard.line_ids[0]
        line.new_quantity = 7.0
        line.new_price_unit = 150.0
        wizard.action_apply()
        po_line = self.po.order_line[0]
        self.assertEqual(po_line.product_qty, 7.0)
        self.assertEqual(po_line.price_unit, 150.0)
        self.assertTrue(po_line.taxes_id)
        self.assertTrue(po_line.price_tax)

    def test_apply_done_po_raises(self):
        order_form = Form(self.env["purchase.order"])
        order_form.partner_id = self.partner_a
        order_form.fiscal_operation_id = self.fiscal_operation
        with order_form.order_line.new() as line:
            line.product_id = self.product_a
            line.fiscal_operation_line_id = self.fiscal_operation_line
        done_po = order_form.save()
        done_po_line = done_po.order_line[0]
        done_po_line.partner_order = "PO-DONE"
        done_po_line.partner_order_line = "1"
        done_po.state = "done"
        wizard_line = self.env["purchase.update.from.nfe.wizard.line"].create(
            {
                "nfe_line_id": self.bill.invoice_line_ids[0].id,
                "po_line_id": done_po_line.id,
                "new_quantity": 5.0,
                "new_price_unit": 10.0,
            }
        )
        with self.assertRaises(UserError):
            wizard_line._apply()

    def test_create_po_from_nfe(self):
        action = self.bill.action_create_po_from_nfe()
        po = self.env["purchase.order"].browse(action["res_id"])
        self.assertEqual(po.partner_id, self.bill.partner_id)
        self.assertEqual(po.partner_ref, "1 / 42")
        self.assertEqual(po.fiscal_operation_id, self.fiscal_operation)
        po_line = po.order_line[0]
        self.assertEqual(po_line.product_id, self.product_a)
        self.assertEqual(po_line.product_qty, self.bill.invoice_line_ids.quantity)
        self.assertEqual(po_line.price_unit, self.bill.invoice_line_ids.price_unit)
        self.assertEqual(po_line.partner_order, "PO-REF-1")
        self.assertEqual(po_line.partner_order_line, "1")
        self.assertTrue(po_line.taxes_id)
        self.assertTrue(po_line.price_tax)
