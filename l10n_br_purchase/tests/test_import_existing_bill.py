# Copyright 2026 - TODAY Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from .test_l10n_br_purchase import L10nBrPurchaseBaseTest


def _nfe_access_key(body):
    """43-digit NF-e key body plus the mod-11 check digit."""
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    total = 0
    for index, digit in enumerate(reversed(body)):
        total += int(digit) * weights[index % 8]
    rest = total % 11
    check = 0 if rest < 2 else 11 - rest
    return body + str(check)


class TestImportPurchaseBill(L10nBrPurchaseBaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document_type_55 = cls.env.ref("l10n_br_fiscal.document_55")
        cls.document_type_se = cls.env.ref("l10n_br_fiscal.document_SE")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.fiscal_operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")
        cls.service_operation_line = cls.env.ref(
            "l10n_br_fiscal.fo_compras_compras_uso_consumo"
        )

    def _key(self, serial):
        body = f"35231149647316000169550010000771061{serial:08d}"
        return _nfe_access_key(body)

    def _confirm(self, order):
        for line in order.order_line:
            line.product_id.purchase_method = "purchase"
        order.with_context(tracking_disable=True).button_confirm()
        return order

    def _official_document(self, bill, key, icms_value=12.34):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": bill.company_id.id,
                "fiscal_operation_id": bill.fiscal_operation_id.id,
                "document_type_id": bill.document_type_id.id,
                "document_serie": bill.document_serie,
                "document_number": "99001",
                "document_date": fields.Date.from_string("2026-08-17"),
                "issuer": "partner",
                "partner_id": bill.partner_id.id,
                "fiscal_operation_type": "in",
                "document_key": key,
                "imported_document": True,
            }
        )
        for invoice_line in bill._importable_invoice_lines():
            fiscal_line = self.env["l10n_br_fiscal.document.line"].create(
                {
                    "document_id": document.id,
                    "name": invoice_line.name,
                    "product_id": invoice_line.product_id.id,
                    "quantity": invoice_line.quantity,
                    "fiscal_operation_type": "in",
                    "fiscal_operation_id": self.fiscal_operation.id,
                    "fiscal_operation_line_id": (
                        invoice_line.fiscal_operation_line_id.id
                    ),
                }
            )
            fiscal_line.price_unit = invoice_line.price_unit
            fiscal_line.quantity = invoice_line.quantity
            fiscal_line.icms_value = icms_value
            purchase_line = invoice_line.purchase_line_id
            if purchase_line and purchase_line.partner_order:
                fiscal_line.partner_order = purchase_line.partner_order
                fiscal_line.partner_order_line = purchase_line.partner_order_line
        return document

    def test_purchase_bill_keeps_the_order_line(self):
        order = self._confirm(self.po_products)
        order.action_create_invoice()
        bill = order.invoice_ids.filtered(lambda move: move.state == "draft")[:1]
        self.assertTrue(bill.invoice_line_ids.purchase_line_id)
        purchase_lines = {
            line.id: line.purchase_line_id for line in bill._importable_invoice_lines()
        }
        key = self._key(1)
        document = self._official_document(bill, key)
        bill._apply_imported_fiscal_document(document, confirm_divergence=True)
        self.assertEqual(bill.document_key, key)
        self.assertTrue(bill.imported_document)
        for line in bill._importable_invoice_lines():
            self.assertEqual(line.purchase_line_id, purchase_lines[line.id])
            self.assertEqual(line.fiscal_document_line_id.document_id, document)
            self.assertAlmostEqual(line.icms_value, 12.34, places=2)

    def test_new_bill_links_the_only_purchase_line(self):
        order = self._confirm(self.po_products)
        document = self._document_from_order(order, self.document_type_55, self._key(2))
        move = self._invoice_from_document(document)
        self.assertFalse(move.invoice_line_ids.purchase_line_id)
        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create({})
        wizard._link_purchase_order_lines(move, document)
        for line in move._importable_invoice_lines():
            purchase_line = order.order_line.filtered(
                lambda item, product=line.product_id: item.product_id == product
            )
            self.assertEqual(line.purchase_line_id, purchase_line)

    def test_service_bill_without_xped_links_the_only_order(self):
        order = self.env.ref("l10n_br_purchase.main_po_only_service")
        self._confirm(order)
        document = self._document_from_order(order, self.document_type_se, key=False)
        for line in document.fiscal_line_ids:
            line.partner_order = False
            line.partner_order_line = False
        move = self._invoice_from_document(document)
        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create({})
        wizard._link_purchase_order_lines(move, document)
        self.assertEqual(move.invoice_line_ids.purchase_line_id, order.order_line)

    def test_service_bill_without_xped_stays_open_when_two_orders_match(self):
        order = self.env.ref("l10n_br_purchase.main_po_only_service")
        self._confirm(order)
        second = order.copy()
        self._confirm(second)
        document = self._document_from_order(order, self.document_type_se, key=False)
        for line in document.fiscal_line_ids:
            line.partner_order = False
            line.partner_order_line = False
        move = self._invoice_from_document(document)
        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create({})
        wizard._link_purchase_order_lines(move, document)
        self.assertFalse(move.invoice_line_ids.purchase_line_id)

    def _document_from_order(self, order, document_type, key):
        operation_line = self.fiscal_operation_line
        if document_type == self.document_type_se:
            operation_line = self.service_operation_line
        document = (
            self.env["l10n_br_fiscal.document"]
            .with_company(order.company_id)
            .create(
                {
                    "company_id": order.company_id.id,
                    "fiscal_operation_id": self.fiscal_operation.id,
                    "document_type_id": document_type.id,
                    "document_serie": "1",
                    "document_number": "77001",
                    "document_date": fields.Date.from_string("2026-08-17"),
                    "issuer": "partner",
                    "partner_id": order.partner_id.id,
                    "fiscal_operation_type": "in",
                    "document_key": key,
                    "imported_document": True,
                }
            )
        )
        for purchase_line in order.order_line:
            fiscal_line = self.env["l10n_br_fiscal.document.line"].create(
                {
                    "document_id": document.id,
                    "name": purchase_line.name,
                    "product_id": purchase_line.product_id.id,
                    "quantity": purchase_line.product_qty,
                    "fiscal_operation_type": "in",
                    "fiscal_operation_id": self.fiscal_operation.id,
                    "fiscal_operation_line_id": operation_line.id,
                }
            )
            fiscal_line.price_unit = purchase_line.price_unit
            fiscal_line.quantity = purchase_line.product_qty
        return document

    def _invoice_from_document(self, document):
        move_form = (
            self.env["account.move"]
            .with_company(document.company_id)
            .import_fiscal_document(document, move_type="in_invoice")
        )
        return self.env["account.move"].browse(move_form.id)
