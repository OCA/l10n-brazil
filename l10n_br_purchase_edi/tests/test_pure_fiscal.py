# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import tagged

from odoo.addons.l10n_br_fiscal_edi.tests.common import readable_field_names

from .common import PurchaseEdiCase


@tagged("post_install", "-at_install")
class TestPureFiscalUser(PurchaseEdiCase):
    """A user of the fiscal group only, with no right on purchases, accounting or
    stock, reads, edits and confirms the imported document while orders exist."""

    def _as_pure_fiscal(self, document):
        user = self._fiscal_user("pure-fiscal")
        # what the tests wrote must reach the database, and the cache of the
        # superuser must not hide a read the user has no right to do
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

    def _open_data(self):
        """An open order of the supplier, the origin suggested and resolved."""
        self._order()
        self._resolve_product()
        self.assertTrue(self.line.import_purchase_line_id)

    def test_the_pure_fiscal_user_reads_edits_and_saves(self):
        self._open_data()
        document = self._as_pure_fiscal(self.document)

        self._read_everything(document)
        document.fiscal_line_ids.write({"name": "Edited by the fiscal user"})
        document.fiscal_line_ids.write({"quantity": 2.0})
        self.env.flush_all()
        self._read_everything(document)

    def test_the_pure_fiscal_user_confirms_the_origins_and_the_suggestions(self):
        self._open_data()
        document = self._as_pure_fiscal(self.document)

        document.action_confirm_import_origins()
        document.action_import_confirm_suggestions()
        self.env.flush_all()

        self.assertEqual(self.line.import_origin_state, "resolved")
        self._read_everything(document)

    def test_the_pure_fiscal_user_changes_the_origin_of_a_line(self):
        self._open_data()
        order_line = self.line.import_purchase_line_id
        order_line.fiscal_operation_line_id = self.env.ref(
            "l10n_br_fiscal.fo_compras_compras_uso_consumo"
        )
        self.line.write({"import_purchase_line_id": False})
        document = self._as_pure_fiscal(self.document)

        # the destination of the order is applied, which looks for a bill
        document.fiscal_line_ids.write({"import_purchase_line_id": order_line.id})
        self.env.flush_all()

        self.assertEqual(self.line.import_origin_state, "resolved")
        self._read_everything(document)
