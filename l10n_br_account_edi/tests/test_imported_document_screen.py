# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.l10n_br_fiscal_edi.tests.common import fiscal_user_group_ids

from .common import AccountEdiCase


@tagged("post_install", "-at_install")
class TestImportedDocumentScreen(AccountEdiCase):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.fiscal_user = cls.env["res.users"].create(
            {
                "name": "Fiscal without accounting",
                "email": "fiscal-no-accounting@example.com",
                "login": "edi_fiscal_no_accounting",
                "company_id": cls.company.id,
                "company_ids": [Command.set(cls.company.ids)],
                "groups_id": [
                    Command.set(fiscal_user_group_ids(cls.env, form_groups=True))
                ],
            }
        )

    def _as_fiscal_user(self, document):
        return document.with_user(self.fiscal_user)

    def _declared_dates(self, document):
        """The date of the file (not at midnight) and no date of entry."""
        document.write({"document_date": "2026-01-10 15:30:00", "date_in_out": False})
        return document.document_date

    def _open(self, document):
        """What the web client asks to open the form: the view, then the values of
        the fields that are in it, for the user."""
        document = self._as_fiscal_user(document)
        arch = etree.fromstring(document.get_view(view_type="form")["arch"])
        names = {
            node.get("name")
            for node in arch.xpath("//form//field")
            if node.get("name") in document._fields
            and not document._fields[node.get("name")].type.endswith("2many")
        }
        return document.read(sorted(names))[0]

    def test_a_fiscal_user_without_accounting_opens_a_received_document(self):
        values = self._open(self._imported_document())

        self.assertEqual(values["document_number"], "100")

    def test_a_fiscal_user_without_accounting_opens_an_own_document(self):
        values = self._open(self._own_imported_document())

        self.assertEqual(values["document_number"], "777")

    def test_the_counter_of_invoices_is_not_read_for_that_user(self):
        document = self._as_fiscal_user(self._imported_document())

        self.assertIn("document_number", document.read(["document_number"])[0])
        arch = document.get_view(view_type="form")["arch"]
        self.assertNotIn("move_count", arch)

    def test_a_fiscal_user_without_accounting_confirms_the_document(self):
        document = self._own_imported_document(confirm=False)

        self._as_fiscal_user(document).action_document_confirm()

        self.assertEqual(document.state_edoc, "autorizada")

    def test_what_belongs_to_the_invoice_is_not_in_the_form_of_that_user(self):
        document = self._imported_document()

        arch = etree.fromstring(
            self._as_fiscal_user(document).get_view(view_type="form")["arch"]
        )

        for name in ("action_generate_invoice", "action_view_invoice"):
            self.assertFalse(arch.xpath(f"//button[@name='{name}']"))
        self.assertFalse(arch.xpath("//field[@name='move_ids']"))
        self.assertFalse(arch.xpath("//field[@name='move_count']"))

    def test_a_document_without_a_fiscal_operation_is_refused_with_a_message(self):
        document = self._imported_document()
        document.fiscal_operation_id = False

        with self.assertRaisesRegex(UserError, "no fiscal operation"):
            document.action_generate_invoice()

    def test_what_the_form_of_the_invoice_refuses_becomes_a_message(self):
        document = self._imported_document()
        model = type(self.env["account.move"])

        with (
            mock.patch.object(
                model,
                "import_fiscal_document",
                side_effect=AssertionError("journal is a required field"),
            ),
            self.assertRaisesRegex(UserError, "journal is a required field"),
        ):
            document.action_generate_invoice()

    def test_a_document_without_a_partner_is_refused_with_a_message(self):
        document = self._imported_document()
        document.partner_id = False

        with self.assertRaisesRegex(UserError, "no partner"):
            document.action_generate_invoice()

    def test_the_dates_of_the_file_survive_the_invoice_of_a_received_document(self):
        document = self._imported_document()
        declared = self._declared_dates(document)

        document.action_generate_invoice()

        self.assertEqual(document.document_date, declared)
        self.assertFalse(document.date_in_out)

    def test_the_dates_of_the_file_survive_the_invoice_of_an_own_document(self):
        document = self._own_imported_document()
        declared = self._declared_dates(document)

        document.action_generate_invoice()

        self.assertEqual(document.document_date, declared)
        self.assertFalse(document.date_in_out)

    def test_the_invoice_is_offered_only_to_a_document_with_something_to_pay(self):
        document = self._imported_document()
        self.assertTrue(document.edi_can_generate_invoice)

        document.fiscal_line_ids.unlink()

        self.assertFalse(document.edi_can_generate_invoice)

    def test_the_invoice_is_not_offered_again_once_it_exists(self):
        document = self._imported_document()
        document.action_generate_invoice()

        self.assertFalse(document.edi_can_generate_invoice)

    def test_the_page_of_installments_is_empty_when_nothing_is_declared(self):
        document = self._imported_document()

        self.assertFalse(document._edi_get_installments())
        self.assertFalse(document.edi_payment_summary)

    def test_the_button_follows_the_computed_flag(self):
        document = self._imported_document()
        arch = etree.fromstring(
            document.with_user(self.env.ref("base.user_admin")).get_view(
                view_type="form"
            )["arch"]
        )

        button = arch.xpath("//button[@name='action_generate_invoice']")

        self.assertIn("edi_can_generate_invoice", button[0].get("modifiers"))

    def _financial_total_zeroed(self, document):
        """What the operation does to some imported documents: the financial total
        of the document is stored as zero, while the lines carry the amounts."""
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE l10n_br_fiscal_document SET amount_financial_total = 0 "
            "WHERE id = %s",
            (document.id,),
        )
        document.invalidate_recordset(["amount_financial_total"])
        self.assertFalse(document.amount_financial_total)
        return document

    def test_the_invoice_is_offered_to_a_received_document_with_an_operation(self):
        document = self._financial_total_zeroed(self._imported_document())

        self.assertTrue(document.edi_can_generate_invoice)

    def test_the_invoice_is_offered_to_a_received_document_without_an_operation(self):
        document = self._imported_document()
        document.fiscal_operation_id = False

        self.assertTrue(document.edi_can_generate_invoice)

    def test_the_invoice_is_offered_to_an_own_document(self):
        document = self._financial_total_zeroed(self._own_imported_document())

        self.assertTrue(document.edi_can_generate_invoice)

    def test_the_invoice_is_offered_to_an_own_document_without_an_operation(self):
        document = self._own_imported_document()
        document.fiscal_operation_id = False

        self.assertTrue(document.edi_can_generate_invoice)

    def _sequences(self):
        return self.env["ir.sequence"].search([]).mapped("number_next_actual")

    def test_an_own_document_without_a_serie_record_is_invoiced(self):
        numbers = self._sequences()
        document = self._own_imported_document(with_serie=False)
        self.assertFalse(document.document_serie_id)

        move = self.env["account.move"].browse(
            document.action_generate_invoice()["res_id"]
        )

        self.assertEqual(move.move_type, "out_invoice")
        self.assertEqual(
            (document.document_serie, document.document_number), ("001", "777")
        )
        self.assertFalse(document.document_serie_id)
        self.assertEqual(self._sequences(), numbers)

    def test_an_own_document_without_a_serie_record_is_confirmed(self):
        numbers = self._sequences()
        document = self._own_imported_document(confirm=False, with_serie=False)

        document.with_user(self.fiscal_user).action_document_confirm()

        self.assertEqual(document.state_edoc, "autorizada")
        self.assertEqual(self._sequences(), numbers)

    def test_a_fiscal_user_without_accounting_edits_saves_and_confirms(self):
        document = self._own_imported_document(confirm=False, with_serie=False)
        document = document.with_user(self.fiscal_user)
        self.env.flush_all()
        self.env.invalidate_all()

        with Form(document) as form:
            form.date_in_out = "2026-01-11 09:45:00"
        self.env.flush_all()
        self.env.invalidate_all()
        document.action_document_confirm()

        self.assertEqual(document.state_edoc, "autorizada")
        self.assertEqual(document.date_in_out.hour, 9)

    def test_the_invoice_is_born_in_the_company_of_the_document(self):
        other = self.company_data_2["company"]
        document = self._imported_document()
        self.assertNotEqual(other, document.company_id)

        # the user has both companies and the other one is the selected
        document = document.with_context(
            allowed_company_ids=[other.id, document.company_id.id]
        )
        self.assertEqual(document.env.company, other)
        move = self.env["account.move"].browse(
            document.action_generate_invoice()["res_id"]
        )

        self.assertEqual(move.company_id, document.company_id)
