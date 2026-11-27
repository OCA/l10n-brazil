# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import tagged

from odoo.addons.l10n_br_fiscal_edi.tests.common import readable_field_names

from .common import StockEdiCase


@tagged("post_install", "-at_install")
class TestPureFiscalUser(StockEdiCase):
    """A user of the fiscal group only reads, edits and saves the imported
    document while an order, a receipt and an invoice of the order exist."""

    def _as_pure_fiscal(self, document):
        user = self._fiscal_user("pure-fiscal-stock")
        # the cache of the superuser must not hide a read the user cannot do
        self.env.flush_all()
        self.env.invalidate_all()
        return document.with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids
        )

    def _read_everything(self, document):
        """The fields of the views, as the form reads them, as the user."""
        lines = document.fiscal_line_ids
        for record in (document, lines):
            arch = etree.fromstring(record.get_view(view_type="form")["arch"])
            names = {node.get("name") for node in arch.iter("field")}
            record.read(readable_field_names(record, names))

    def test_the_pure_fiscal_user_with_an_order_and_a_receipt(self):
        order = self._order(quantity=10)
        self._receive(order, 4, backorder=True)
        self.line.write({"quantity": 3, "uom_id": self.unit.id})
        self._resolve_product()
        self.assertTrue(self.line.import_stock_move_id)
        document = self._as_pure_fiscal(self.document)

        self._read_everything(document)
        document.fiscal_line_ids.write({"name": "Edited by the fiscal user"})
        self.env.flush_all()
        self._read_everything(document)
        self.assertTrue(document.import_divergent in (True, False))

    def test_the_pure_fiscal_user_with_a_bill_of_the_order(self):
        order = self._order(quantity=10)
        self._receive(order, 10)
        self.line.write({"quantity": 3, "uom_id": self.unit.id})
        self._resolve_product()
        self.line.import_purchase_line_id = order.order_line
        other = self._imported_document(lines=[{"quantity": 2}])
        self._resolve_product(other.fiscal_line_ids)
        other.fiscal_line_ids.import_purchase_line_id = order.order_line
        other.action_generate_invoice()
        document = self._as_pure_fiscal(self.document)

        self._read_everything(document)
        document.fiscal_line_ids.write({"quantity": 4})
        self._read_everything(document)
