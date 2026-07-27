# Copyright (C) 2026  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestDocumentImportCheck(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.product = cls.env["product.product"].create(
            {"name": "Amostra Teste", "uom_id": cls.env.ref("uom.product_uom_unit").id}
        )
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": cls.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                "fiscal_operation_type": "in",
                "imported_document": True,
            }
        )
        cls.line = cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": cls.document.id,
                "name": "Amostra gratis",
                "product_id": cls.product.id,
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "quantity": 1.0,
                "price_unit": 0.0,
            }
        )

    def test_free_line_is_allowed(self):
        """A 100% free line (zero unit price AND zero amounts, e.g. a
        bonification or free sample declared with vUnCom=0) must not block
        the account move generation."""
        self.assertFalse(self.line.fiscal_amount_total)
        self.document._check_document_import()  # must not raise

    def test_zero_price_with_amounts_is_blocked(self):
        """A zero unit price on a line that still carries amounts is an
        unresolved de-para (inconsistent data) and must keep blocking."""
        self.line.freight_value = 100.0
        self.assertTrue(self.line.fiscal_amount_total)
        with self.assertRaises(UserError):
            self.document._check_document_import()

    def test_missing_product_is_blocked(self):
        self.line.price_unit = 10.0
        self.line.product_id = False
        with self.assertRaises(UserError):
            self.document._check_document_import()
