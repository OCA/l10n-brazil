# Copyright (C) 2026  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from unittest import mock

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.models.document_line import DocumentLine


def _fiscal_name(lines):
    for line in lines:
        line.name = "name of the fiscal compute"


class TestDocumentLineName(TransactionCase):
    def test_name_of_a_line_without_invoice_line_is_left_to_the_fiscal_compute(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                "fiscal_operation_type": "in",
            }
        )
        product = self.env["product.product"].create({"name": "Product"})
        line = self.env["l10n_br_fiscal.document.line"].create(
            {"document_id": document.id, "name": "Declared name", "quantity": 1}
        )

        with mock.patch.object(DocumentLine, "_compute_name", autospec=True) as base:
            base.side_effect = _fiscal_name
            line.product_id = product
            name = line.name

        self.assertEqual(name, "name of the fiscal compute")
