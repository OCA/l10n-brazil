# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import UserError, ValidationError

from .common import PurchaseEdiCase


class TestOrigin(PurchaseEdiCase):
    def test_declared_reference_resolves_the_origin(self):
        order = self._order()
        self.line.write({"partner_order": order.name, "partner_order_line": "1"})
        self._resolve_product()

        self.assertEqual(self.line.import_purchase_line_id, order.order_line)
        self.assertEqual(self.line.import_origin_state, "resolved")

    def test_only_open_line_of_the_product_is_suggested(self):
        order = self._order()
        self._resolve_product()

        self.assertEqual(self.line.import_purchase_line_id, order.order_line)
        self.assertEqual(self.line.import_origin_state, "suggested")
        # what the supplier declared stays as it came
        self.assertFalse(self.line.partner_order)

    def test_two_candidates_stay_pending(self):
        self._order()
        self._order()
        self._resolve_product()

        self.assertFalse(self.line.import_purchase_line_id)
        self.assertEqual(self.line.import_origin_state, "pending")

    def test_a_document_without_operation_still_gets_the_suggestion(self):
        self.document.fiscal_operation_id = False
        order = self._order()
        self._resolve_product()

        self.assertEqual(self.line.import_purchase_line_id, order.order_line)
        self.assertEqual(self.line.import_origin_state, "suggested")

    def test_supplier_without_open_orders_leaves_no_state(self):
        self._resolve_product()

        self.assertFalse(self.line.import_origin_state)

    def test_order_of_another_supplier_is_not_a_candidate(self):
        self._order(partner=self.company.partner_id)
        self._resolve_product()

        self.assertFalse(self.line.import_origin_state)

    def test_a_decision_is_never_replaced(self):
        self._order()
        self._resolve_product()
        self.line.write(
            {"import_purchase_line_id": False, "import_origin_state": "no_order"}
        )
        self.line._suggest_import_origin()
        self.assertEqual(self.line.import_origin_state, "no_order")
        self.assertFalse(self.line.import_purchase_line_id)

        self.line.import_origin_state = "resolved"
        self.line._suggest_import_origin()
        self.assertEqual(self.line.import_origin_state, "resolved")

    def test_choosing_the_order_line_resolves_it(self):
        order = self._order()
        self._order()
        self._resolve_product()

        self.line.import_purchase_line_id = order.order_line

        self.assertEqual(self.line.import_origin_state, "resolved")

    def test_confirm_origins_resolves_the_suggestions(self):
        self._order()
        self._resolve_product()
        self.assertTrue(self.document.has_suggested_import_origin)

        self.document.action_confirm_import_origins()

        self.assertEqual(self.line.import_origin_state, "resolved")
        self.assertFalse(self.document.has_suggested_import_origin)

    def test_balance_discounts_the_claims_of_other_documents(self):
        order = self._order(quantity=10)
        other = self._imported_document()
        other_line = other.fiscal_line_ids
        other_line.write({"quantity": 10, "uom_id": self.unit.id})
        other_line.import_purchase_line_id = order.order_line
        self.assertEqual(other_line.import_origin_state, "resolved")
        self._resolve_product()

        # the other document holds all 10: nothing is left for this one
        self.assertFalse(self.line.import_purchase_line_id)
        self.assertEqual(self.line.import_origin_state, "pending")
        self.assertFalse(self._rows(purchase_line_id=order.order_line.id))

        other_line.quantity = 9
        self.line._suggest_import_origin()
        self.assertEqual(self.line.import_origin_state, "suggested")
        row = self._rows(purchase_line_id=order.order_line.id)
        self.assertEqual(row.open_quantity, 1)

    def test_resolved_origin_takes_the_destination_of_the_order(self):
        order = self._order()
        destination = self.env.ref("l10n_br_fiscal.fo_compras_compras_uso_consumo")
        order.order_line.fiscal_operation_line_id = destination
        self._resolve_product()
        self.assertNotEqual(self.line.fiscal_operation_line_id, destination)

        self.document.action_confirm_import_origins()

        self.assertEqual(self.line.fiscal_operation_line_id, destination)

    def test_the_import_suggestion_resolves_the_declared_origin_and_the_destination(
        self,
    ):
        order = self._order()
        destination = self.env.ref("l10n_br_fiscal.fo_compras_compras_uso_consumo")
        order.order_line.fiscal_operation_line_id = destination
        document = self._imported_document(
            lines=[
                {
                    "product_id": self.product.id,
                    "partner_cfop_id": False,
                    "partner_order": order.name,
                    "partner_order_line": "1",
                }
            ]
        )

        document._edi_import_suggest()

        line = document.fiscal_line_ids
        self.assertEqual(line.import_origin_state, "resolved")
        self.assertEqual(line.import_purchase_line_id, order.order_line)
        self.assertEqual(line.fiscal_operation_line_id, destination)

    def test_a_line_resolved_by_the_depara_gets_its_origin(self):
        order = self._order()
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.supplier.id,
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "product_code": "SUP-1",
            }
        )
        document = self._imported_document(
            lines=[{"partner_order": order.name, "partner_order_line": "1"}]
        )

        with self._supplier_code("SUP-1"):
            document._edi_import_suggest()

        line = document.fiscal_line_ids
        self.assertEqual(line.import_state, "resolved")
        self.assertEqual(line.import_purchase_line_id, order.order_line)
        self.assertEqual(line.import_origin_state, "resolved")

    def test_a_line_matched_by_the_supplier_code_and_declared_by_the_order_resolves(
        self,
    ):
        # the buyer mapped the code of the supplier, in a unit that is not the
        # declared one: the order the file declares explains the unit
        self.product.uom_po_id = self.env.ref("uom.product_uom_dozen")
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.supplier.id,
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "product_code": "SUP-1",
            }
        )
        order = self._order()
        order.order_line.product_uom = self.unit
        document = self._imported_document(
            lines=[{"partner_order": order.name, "partner_order_line": "1"}]
        )

        with self._supplier_code("SUP-1"):
            document._edi_import_suggest()

        line = document.fiscal_line_ids
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.import_state, "resolved")
        self.assertEqual(line.import_purchase_line_id, order.order_line)

    def test_a_line_matched_by_the_supplier_code_without_the_order_only_matches(
        self,
    ):
        self.product.uom_po_id = self.env.ref("uom.product_uom_dozen")
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.supplier.id,
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "product_code": "SUP-1",
            }
        )
        self._order()
        document = self._imported_document(lines=[{}])

        with self._supplier_code("SUP-1"):
            document._edi_import_suggest()

        line = document.fiscal_line_ids
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.import_state, "matched")

    def test_the_position_of_nitemped_ignores_sections_and_notes(self):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.supplier.id,
                "company_id": self.company.id,
                "order_line": [
                    Command.create(
                        {
                            "display_type": "line_section",
                            "name": "Section",
                            "sequence": 1,
                            "product_qty": 0,
                        }
                    ),
                    Command.create(
                        {
                            "display_type": "line_note",
                            "name": "Note",
                            "sequence": 2,
                            "product_qty": 0,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "name": "the item",
                            "product_qty": 5,
                            "product_uom": self.unit.id,
                            "price_unit": 10,
                            "sequence": 3,
                        }
                    ),
                ],
            }
        )
        order.button_confirm()
        self.line.write({"partner_order": order.name, "partner_order_line": "1"})
        self._resolve_product()

        self.assertEqual(self.line.import_purchase_line_id.name, "the item")
        self.assertEqual(self.line.import_origin_state, "resolved")

    def test_an_ambiguous_xped_does_not_resolve(self):
        # xPed is a Char(15): two orders that share its first 15 characters
        first = self._order()
        second = self._order()
        first.name = "PO-TRUNCATED-01"
        second.name = "PO-TRUNCATED-012"
        self.line.write({"partner_order": "PO-TRUNCATED-01", "partner_order_line": "1"})
        self._resolve_product()

        self.assertNotEqual(self.line.import_origin_state, "resolved")

    def _declared(self, order_name, item="1", **values):
        """A document whose line declares the order and the item and has no
        product: the reader found none that the company knows."""
        line = {"partner_order": order_name, "partner_order_line": item}
        line.update(values)
        document = self._imported_document(lines=[line])
        document.fiscal_line_ids.write({"product_id": False})
        return document

    def test_the_declared_item_gives_the_product_and_resolves_the_line(self):
        order = self._order()
        document = self._declared(order.name)

        document._edi_import_suggest()

        line = document.fiscal_line_ids
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.import_state, "resolved")
        self.assertEqual(line.import_origin_state, "resolved")
        self.assertEqual(line.import_purchase_line_id, order.order_line)

    def test_the_unit_of_the_order_is_used_when_the_file_declares_an_unknown_one(
        self,
    ):
        order = self._order()
        document = self._declared(order.name, partner_uom_code="ZZZ")

        document._edi_import_suggest()

        line = document.fiscal_line_ids
        self.assertEqual(line.import_state, "resolved")
        self.assertEqual(line.uom_id, order.order_line.product_uom)

    def test_a_declared_unit_that_the_order_does_not_explain_stays_for_the_review(
        self,
    ):
        self.env.ref("uom.product_uom_dozen").code = "DZ"
        order = self._order()
        document = self._declared(order.name, partner_uom_code="DZ")

        document._edi_import_suggest()

        line = document.fiscal_line_ids
        self.assertEqual(line.product_id, self.product)
        self.assertNotEqual(line.import_state, "resolved")

    def test_two_candidates_do_not_give_the_product(self):
        first = self._order()
        second = self._order()
        first.name = "PO-TRUNCATED-01"
        second.name = "PO-TRUNCATED-012"
        document = self._declared("PO-TRUNCATED-01")

        document._edi_import_suggest()

        line = document.fiscal_line_ids
        self.assertFalse(line.product_id)
        self.assertNotEqual(line.import_state, "resolved")

    def test_an_order_of_another_supplier_does_not_give_the_product(self):
        other = self.env["res.partner"].create({"name": "Other supplier"})
        order = self._order(partner=other)
        document = self._declared(order.name)

        document._edi_import_suggest()

        line = document.fiscal_line_ids
        self.assertFalse(line.product_id)
        self.assertFalse(line.import_purchase_line_id)

    def test_a_quotation_does_not_give_the_product(self):
        order = self._order(confirm=False)
        document = self._declared(order.name)

        document._edi_import_suggest()

        line = document.fiscal_line_ids
        self.assertFalse(line.product_id)
        self.assertFalse(line.import_purchase_line_id)

    def test_an_order_without_the_item_does_not_give_the_product(self):
        order = self._order()
        document = self._declared(order.name, item="")

        document._edi_import_suggest()

        self.assertFalse(document.fiscal_line_ids.product_id)

    def test_another_product_chosen_for_the_line_is_kept(self):
        order = self._order()
        other = self.env["product.product"].create({"name": "Chosen product"})
        document = self._declared(order.name)
        document.fiscal_line_ids.product_id = other

        document._edi_import_suggest()

        self.assertEqual(document.fiscal_line_ids.product_id, other)

    def test_the_server_validates_the_origin_the_client_only_suggests(self):
        other_supplier = self._order(partner=self.company.partner_id)
        self._resolve_product()
        with self.assertRaisesRegex(ValidationError, "not of the company"):
            self.line.import_purchase_line_id = other_supplier.order_line

        other_company = (
            self.env["purchase.order"]
            .with_company(self.other_company)
            .create(
                {
                    "partner_id": self.supplier.id,
                    "company_id": self.other_company.id,
                    "order_line": [
                        Command.create(
                            {
                                "product_id": self.product.id,
                                "name": "x",
                                "product_qty": 1,
                                "product_uom": self.unit.id,
                                "price_unit": 1,
                            }
                        )
                    ],
                }
            )
        )
        with self.assertRaisesRegex(ValidationError, "not of the company"):
            self.line.import_purchase_line_id = other_company.order_line

        other_product = self.env["product.product"].create({"name": "Other"})
        order = self._order()
        self.line.product_id = other_product
        with self.assertRaisesRegex(ValidationError, "not of the product"):
            self.line.import_purchase_line_id = order.order_line

    def test_a_document_issued_by_the_company_is_not_a_purchase(self):
        quote = self._order(confirm=False)
        sale = self.env.ref("l10n_br_fiscal.fo_venda").id
        # the operation of a sale, or an issuer that says it is a sale whatever
        # the operation
        documents = self.Document
        for values in ({"fiscal_operation_id": sale}, {}):
            documents |= self._imported_document(
                lines=[{"product_id": self.product.id}],
                issuer="company",
                partner_id=self.supplier.id,
                **values,
            )
        line = documents.fiscal_line_ids

        quote.button_confirm()
        documents._edi_import_suggest()

        self.assertFalse(line.import_purchase_line_id)
        self.assertFalse(any(line.mapped("import_origin_state")))
        self.assertFalse(self._rows(fiscal_document_id=documents.ids[0]))
        self.assertFalse(self._rows(fiscal_document_id=documents.ids[1]))

    def test_the_confirmation_of_an_order_does_not_reach_a_document_of_the_company(
        self,
    ):
        quote = self._order(confirm=False)
        document = self._imported_document(
            lines=[{"product_id": self.product.id}],
            issuer="company",
            partner_id=self.supplier.id,
        )

        quote.button_confirm()

        self.assertFalse(document.fiscal_line_ids.import_purchase_line_id)

    def test_destination_does_not_replace_a_manual_choice(self):
        order = self._order()
        destination = self.env.ref("l10n_br_fiscal.fo_compras_compras_uso_consumo")
        order.order_line.fiscal_operation_line_id = destination
        asset = self.env.ref("l10n_br_fiscal.fo_compras_compras_ativo")
        self._resolve_product()
        self.line.fiscal_operation_line_id = asset

        self.document.action_confirm_import_origins()

        self.assertEqual(self.line.fiscal_operation_line_id, asset)

    def test_order_line_name_shows_the_order(self):
        order = self._order()

        self.assertIn(order.name, order.order_line.display_name)
        found = self.env["purchase.order.line"].name_search(order.name)
        self.assertIn(order.order_line.id, [line_id for line_id, _name in found])

    def test_generate_invoice_refuses_an_undecided_origin(self):
        self._order()
        self._resolve_product()

        with self.assertRaisesRegex(UserError, "Confirm Suggestions"):
            self.document.action_generate_invoice()
