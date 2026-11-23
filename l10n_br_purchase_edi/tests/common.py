# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo import Command, fields

from odoo.addons.l10n_br_fiscal_edi.tests.common import EdiImportCase


class PurchaseEdiCase(EdiImportCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.unit = cls.uom_unit
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.product = cls.env["product.product"].create(
            {"name": "Reviewed product", "detailed_type": "consu"}
        )
        cls.Match = cls.env["l10n_br_purchase_edi.match"]
        cls.document = cls._create_imported_document(
            cls,
            lines=[{"price_unit": 140.0}],
            document_type_id=cls.env.ref("l10n_br_fiscal.document_SE").id,
            document_serie="1",
            document_number="100",
            document_date="2026-01-10 12:00:00",
        )
        cls.line = cls.document.fiscal_line_ids

    def _imported_document(self, **values):
        """Another imported document, of a type no reader of the scope handles."""
        values.setdefault(
            "document_type_id", self.env.ref("l10n_br_fiscal.document_SE").id
        )
        values.setdefault("document_serie", "1")
        values.setdefault("document_number", str(self.Document.search_count([]) + 1000))
        return self._create_imported_document(**values)

    def _order(self, quantity=10.0, price=140.0, confirm=True, partner=None):
        order = self.env["purchase.order"].create(
            {
                "partner_id": (partner or self.supplier).id,
                "company_id": self.company.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "name": self.product.name,
                            "product_qty": quantity,
                            "product_uom": self.unit.id,
                            "price_unit": price,
                            "date_planned": fields.Datetime.now(),
                        }
                    )
                ],
            }
        )
        if confirm:
            order.button_confirm()
        return order

    def _resolve_product(self, line=None):
        (line or self.line)._apply_import_depara(
            product=self.product, uom=self.unit, fiscal_operation=self.operation
        )

    def _supplier_code(self, code):
        """The supplier code the reader would find on the lines."""
        return mock.patch.object(
            type(self.env["l10n_br_fiscal.document.line"]),
            "_get_partner_product_code",
            return_value=code,
        )

    def _rows(self, **domain):
        # the read model is SQL: what the test wrote has to reach the database
        self.env.flush_all()
        self.env.invalidate_all()
        return self.Match.search([(key, "=", value) for key, value in domain.items()])
