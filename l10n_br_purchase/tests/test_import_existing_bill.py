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


class _PurchaseMatchLine:
    """Fields ``_match_purchase_line`` reads from a fiscal line."""

    def __init__(self, company, order_ref, item, product):
        self.company_id = company
        self.partner_order = order_ref or ""
        self.partner_order_line = item or ""
        self.product_id = product


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

    def test_xped_name_and_position_links_each_purchase_line(self):
        order = self._copied_product_order(same_product=True)
        product_lines = self._product_lines(order)
        self.assertEqual(len(product_lines), 2)
        for position, purchase_line in enumerate(product_lines, start=1):
            self.assertEqual(
                self._match_xped(order, order.name, str(position)),
                purchase_line,
            )

    def test_xped_vendor_reference_and_position_links_each_purchase_line(self):
        order = self._copied_product_order(same_product=True)
        order.partner_ref = "VENDOR-REF-1"
        self.assertNotEqual(order.name, order.partner_ref)
        product_lines = self._product_lines(order)
        for position, purchase_line in enumerate(product_lines, start=1):
            self.assertEqual(
                self._match_xped(order, order.partner_ref, str(position)),
                purchase_line,
            )

    def test_partner_order_on_the_line_links_when_the_po_name_differs(self):
        order = self._copied_product_order()
        target = self._product_lines(order)[1]
        target.partner_order = "SUP-99"
        target.partner_order_line = "7"
        self.assertNotEqual(order.name, "SUP-99")
        self.assertEqual(self._match_xped(order, "SUP-99", "7"), target)

    def test_divergent_purchase_keys_leave_the_line_open(self):
        order = self._copied_product_order()
        second = self._product_lines(order)[1]
        second.partner_order = order.name
        second.partner_order_line = "1"
        self.assertFalse(self._match_xped(order, order.name, "1"))

    def test_xped_name_without_item_stays_open_when_several_lines_match(self):
        order = self._copied_product_order()
        self.assertGreater(len(self._product_lines(order)), 1)
        self.assertFalse(self._match_xped(order, order.name, ""))

    def test_xped_position_skips_a_section_line(self):
        order = self.po_products.copy()
        # purchase.order.line._order is sequence, id. A line created after the
        # order is copied is appended to the cached one2many, so give the
        # section a lower sequence and read the lines again.
        self.env["purchase.order.line"].create(
            {
                "order_id": order.id,
                "name": "Section",
                "display_type": "line_section",
                "sequence": min(order.order_line.mapped("sequence")) - 1,
                "product_id": False,
                "product_qty": 0.0,
                "product_uom": False,
                "price_unit": 0.0,
                "date_planned": False,
            }
        )
        order.invalidate_recordset(["order_line"])
        self._confirm(order)
        product_lines = self._product_lines(order)
        self.assertEqual(order.order_line[0].display_type, "line_section")
        self.assertEqual(len(product_lines), 2)
        self.assertEqual(self._match_xped(order, order.name, "1"), product_lines[0])

    def _copied_product_order(self, same_product=False):
        order = self.po_products.copy()
        if same_product:
            order.order_line[1:].write(
                {"product_id": order.order_line[0].product_id.id}
            )
        return self._confirm(order)

    def _product_lines(self, order):
        return order.order_line.filtered(lambda line: not line.display_type)

    def _match_xped(self, order, order_ref, item, product=None):
        fiscal_line = _PurchaseMatchLine(
            order.company_id,
            order_ref,
            item,
            product or self.env["product.product"],
        )
        wizard = self.env["l10n_br_fiscal.document.import.wizard"].new({})
        return wizard._match_purchase_line(fiscal_line, order.partner_id)

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
        for purchase_line in order.order_line.filtered(
            lambda line: not line.display_type
        ):
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
