# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import tagged

from odoo.addons.l10n_br_fiscal_edi.tests.common import readable_field_names

from .common import RequestEdiCase


@tagged("post_install", "-at_install")
class TestPureFiscalUser(RequestEdiCase):
    """A user of the fiscal group only reads, edits and saves the imported
    document while requests and the order created from one exist."""

    def _as_pure_fiscal(self, document):
        user = self._fiscal_user("pure-fiscal-request")
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

    def test_the_pure_fiscal_user_with_a_request_and_its_order(self):
        request = self._request()
        self.line.write({"quantity": 4, "price_unit": 125.0, "uom_id": self.unit.id})
        self._resolve_product()
        self._note_rows_and_request(request).action_create_order_from_request()
        self.assertTrue(self.line.sudo().import_request_line_id)
        self._request()
        document = self._as_pure_fiscal(self.document)

        self._read_everything(document)
        document.fiscal_line_ids.write({"name": "Edited by the fiscal user"})
        self.env.flush_all()
        self._read_everything(document)
