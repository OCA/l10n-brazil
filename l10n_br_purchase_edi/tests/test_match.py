# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.exceptions import UserError

from .common import PurchaseEdiCase


class TestMatch(PurchaseEdiCase):
    def _open(self):
        domain = self.document.action_open_origin_match()["domain"]
        self.env.flush_all()
        return self.Match.search(domain)

    def test_the_tela_lists_the_note_and_the_order_with_encoded_ids(self):
        order = self._order(quantity=10)
        self._resolve_product()

        rows = self._open()

        note = rows.filtered(lambda row: row.kind == "note")
        pending = rows.filtered(lambda row: row.kind == "order")
        self.assertEqual(note.id, 4 * self.line.id)
        self.assertEqual(pending.id, 4 * order.order_line.id + 1)
        self.assertEqual(pending.open_quantity, 10)
        self.assertEqual(note.reference, self.document.document_number)

    def test_the_tela_is_filtered_by_company_and_supplier(self):
        other = self._order(partner=self.company.partner_id)
        self._resolve_product()

        self.assertNotIn(other.order_line.id, self._open().purchase_line_id.ids)

    def test_match_resolves_and_a_pending_product_takes_the_order_one(self):
        order = self._order()
        rows = self._rows(fiscal_document_id=self.document.id)
        rows |= self._rows(purchase_line_id=order.order_line.id)

        rows.action_match()

        self.assertEqual(self.line.import_purchase_line_id, order.order_line)
        self.assertEqual(self.line.import_origin_state, "resolved")
        self.assertEqual(self.line.product_id, self.product)
        self.assertEqual(self.line.uom_id, self.unit)

    def test_match_refuses_what_does_not_fit(self):
        order = self._order()
        other_supplier = self._order(partner=self.company.partner_id)
        note = self._rows(fiscal_document_id=self.document.id)
        with self.assertRaisesRegex(UserError, "another supplier"):
            (
                note | self._rows(purchase_line_id=other_supplier.order_line.id)
            ).action_match()
        self._resolve_product()
        self.line.product_id = self.env["product.product"].create({"name": "Other"})
        with self.assertRaisesRegex(UserError, "not the product"):
            (note | self._rows(purchase_line_id=order.order_line.id)).action_match()
        with self.assertRaisesRegex(UserError, "one order line"):
            note.action_match()

    def test_match_refuses_a_unit_that_does_not_convert(self):
        order = self._order()
        note = self._rows(fiscal_document_id=self.document.id)
        kilogram = self.env.ref("uom.product_uom_kgm")
        self.line.write({"uom_id": kilogram.id, "import_uom_id": kilogram.id})

        with self.assertRaisesRegex(UserError, "does not convert"):
            (note | self._rows(purchase_line_id=order.order_line.id)).action_match()

    def test_a_unit_nobody_confirmed_is_not_converted_silently(self):
        order = self._order()
        self.line.write({"partner_uom_code": "XYZ", "uom_id": False})
        rows = self._rows(fiscal_document_id=self.document.id)
        both = rows | self._rows(purchase_line_id=order.order_line.id)

        with self.assertRaisesRegex(UserError, "was not confirmed"):
            both.action_match()
        with self.assertRaisesRegex(UserError, "was not confirmed"):
            rows.action_create_order()
        self.assertFalse(self.line.import_origin_state == "resolved")

        # the person chose the unit on the line: now it converts
        self.line.write({"uom_id": self.unit.id, "import_uom_id": self.unit.id})
        both.action_match()
        self.assertEqual(self.line.import_origin_state, "resolved")

    def test_one_document_at_a_time(self):
        other = self._imported_document()
        other.fiscal_operation_id = self.operation
        rows = self._rows(fiscal_document_id=self.document.id)
        rows |= self._rows(fiscal_document_id=other.id)

        with self.assertRaisesRegex(UserError, "one document"):
            rows.action_no_order()

    def test_undo_and_without_order_are_recorded(self):
        order = self._order()
        self._resolve_product()
        note = self._rows(fiscal_document_id=self.document.id)

        note.action_no_order()
        self.assertEqual(self.line.import_origin_state, "no_order")
        self.assertIn("without purchase order", self.document.message_ids[0].body)

        note.action_undo()
        self.assertEqual(self.line.import_origin_state, "pending")
        self.assertFalse(self.line.import_purchase_line_id)
        self.assertTrue(self._rows(purchase_line_id=order.order_line.id))

    def test_a_quotation_is_a_candidate_but_cannot_be_matched(self):
        quote = self._order(price=130, confirm=False)
        self._resolve_product()
        rows = self._open().with_context(match_document_id=self.document.id)

        row = rows.filtered(lambda row: row.kind == "quote")
        note = rows.filtered(lambda row: row.kind == "note")
        self.assertEqual(row.purchase_line_id, quote.order_line)
        self.assertEqual(row.price_difference, -10)
        with self.assertRaisesRegex(UserError, "confirms the order"):
            (note | row).action_match()

        action = row.action_open_quote()
        self.assertEqual(action["res_id"], quote.id)

    def test_confirming_the_quotation_suggests_the_origin(self):
        quote = self._order(confirm=False)
        self._resolve_product()
        self.assertFalse(self.line.import_origin_state)

        quote.button_confirm()

        self.assertEqual(self.line.import_purchase_line_id, quote.order_line)
        self.assertEqual(self.line.import_origin_state, "suggested")

    def test_a_document_without_operation_is_in_the_tela_and_follows_the_order(self):
        # without the operation the purpose of the document is empty too
        self.document.write({"fiscal_operation_id": False, "edoc_purpose": False})
        quote = self._order(confirm=False)
        self._resolve_product()
        self.assertTrue(self._rows(fiscal_document_id=self.document.id))

        quote.button_confirm()

        self.assertEqual(self.line.import_origin_state, "suggested")

    def test_create_the_order_from_the_note(self):
        self._resolve_product()
        note = self._rows(fiscal_document_id=self.document.id)

        action = note.action_create_order()

        order = self.env["purchase.order"].browse(action["res_id"])
        self.assertEqual(order.state, "draft")
        self.assertEqual(order.partner_id, self.supplier)
        self.assertEqual(order.order_line.product_id, self.product)
        self.assertEqual(order.order_line.price_unit, self.line.price_unit)
        self.assertEqual(order.order_line.product_qty, self.line.quantity)
        self.assertIn(self.document.display_name, order.origin)
        self.assertFalse(self.line.import_origin_state)

        order.button_confirm()

        self.assertEqual(self.line.import_purchase_line_id, order.order_line)
        self.assertEqual(self.line.import_origin_state, "suggested")

    def test_create_the_order_needs_the_product(self):
        note = self._rows(fiscal_document_id=self.document.id)

        with self.assertRaisesRegex(UserError, "product"):
            note.action_create_order()

    def test_the_tela_follows_the_company_rule(self):
        # a link module may add its own rule for its source
        rules = self.env["ir.rule"].search([("model_id.model", "=", self.Match._name)])
        self.assertTrue(any("company_ids" in rule.domain_force for rule in rules))

    def _extra_source(self, kind="note", **columns):
        """One row of a source of another module, with the extra column."""
        values = dict(
            company_id="NULL::integer",
            partner_id="NULL::integer",
            product_id="NULL::integer",
            uom_id="NULL::integer",
            currency_id="NULL::integer",
            fiscal_document_id="NULL::integer",
            fiscal_line_id="NULL::integer",
            purchase_order_id="NULL::integer",
            purchase_line_id="NULL::integer",
            suggested_purchase_line_id="NULL::integer",
        )
        values.update(columns)
        return (
            f"SELECT 2000000003 AS id, '{kind}' AS kind, 'x'::varchar AS description, "
            "NULL::varchar AS declared_reference, 1.0::float AS quantity, "
            "1.0::float AS open_quantity, 1.0::float AS price_unit, "
            "'r'::varchar AS reference, NULL::date AS date, "
            "'none'::varchar AS line_state, 7 AS extra_flag, "
            + ", ".join(f"{value} AS {name}" for name, value in values.items())
        )

    def test_a_source_of_another_module_adds_its_rows_and_columns(self):
        self._order()
        self._resolve_product()
        self.env.flush_all()
        model = type(self.Match)
        sources = self.Match._match_sources()
        with mock.patch.object(
            model, "_match_extra_columns", return_value={"extra_flag": "integer"}
        ), mock.patch.object(
            model,
            "_match_sources",
            return_value=sources + [(self._extra_source(), ("extra_flag",))],
        ):
            self.env.cr.execute(
                "SELECT id, extra_flag FROM (%s) t ORDER BY id"
                % self.Match._table_query
            )
            rows = dict(self.env.cr.fetchall())

        self.assertEqual(rows[2000000003], 7)
        self.assertTrue(len(rows) > 2)
        self.assertEqual(
            {flag for row_id, flag in rows.items() if row_id != 2000000003}, {None}
        )

    def test_a_row_without_partner_is_listed_for_the_supplier_of_the_document(self):
        self._resolve_product()
        self.env.flush_all()
        model = type(self.Match)
        extra = self._extra_source(
            kind="order",
            company_id=str(self.company.id),
            product_id=str(self.product.id),
        )
        with mock.patch.object(
            model, "_match_extra_columns", return_value={"extra_flag": "integer"}
        ), mock.patch.object(
            model,
            "_match_sources",
            return_value=self.Match._match_sources() + [(extra, ("extra_flag",))],
        ):
            domain = self.document.action_open_origin_match()["domain"]
            found = self.Match.search(domain)

        self.assertIn(2000000003, found.ids)

    def test_creating_an_order_does_not_write_on_the_partner(self):
        self._resolve_product()
        partner = self.supplier
        before = (partner.name, partner.write_date)
        note = self._rows(fiscal_document_id=self.document.id)

        action = note.action_create_order()

        order = self.env["purchase.order"].browse(action["res_id"])
        self.assertEqual(order.partner_id, partner)
        self.assertEqual((partner.name, partner.write_date), before)

    def test_the_order_row_shows_the_note_and_the_difference_side_by_side(self):
        order = self._order(quantity=10, price=4.0)
        self.line.write({"quantity": 8, "price_unit": 4.5, "uom_id": self.unit.id})
        self._resolve_product()

        rows = self._open().with_context(match_document_id=self.document.id)

        row = rows.filtered(lambda row: row.purchase_line_id == order.order_line)
        self.assertEqual((row.note_quantity, row.note_price_unit), (8, 4.5))
        self.assertEqual(row.quantity_difference, -2)
        self.assertAlmostEqual(row.price_difference, -0.5)
        self.assertAlmostEqual(row.price_difference_percent, -100 * 0.5 / 4.5)
        note = rows.filtered(lambda row: row.kind == "note")
        self.assertEqual(note.price_difference, 0)

    def test_the_tela_says_why_nothing_was_suggested(self):
        first = self._order()
        second = self._order()
        self._resolve_product()
        self.assertEqual(self.line.import_origin_state, "pending")

        rows = self._open().with_context(match_document_id=self.document.id)

        note = rows.filtered(lambda row: row.kind == "note")
        orders = rows.filtered(lambda row: row.kind == "order")
        self.assertEqual(note.hint, "2 possible order lines: choose one")
        self.assertEqual(orders.purchase_line_id, first.order_line | second.order_line)

    def test_a_fully_invoiced_order_is_not_a_candidate(self):
        order = self._order(quantity=1)
        other = self._imported_document(lines=[{"quantity": 1}])
        other_line = other.fiscal_line_ids
        self._resolve_product(other_line)
        other_line.import_purchase_line_id = order.order_line
        other.action_generate_invoice()
        self.assertEqual(order.order_line.qty_invoiced, 1)

        self._resolve_product()

        self.assertFalse(self._rows(purchase_line_id=order.order_line.id))
        self.assertFalse(self.line.import_purchase_line_id)
        # nothing to choose from: it does not hold the invoice
        self.assertFalse(self.line.import_origin_candidate_ids)
        self.assertFalse(self.document._import_undecided_origin_lines())
