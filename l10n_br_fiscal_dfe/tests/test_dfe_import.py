# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tools import mute_logger

from odoo.addons.l10n_br_fiscal_edi.tests.common import (
    KEY_1,
    KEY_2,
    EdiImportCase,
)

from .test_dfe_base import _nfe_access_key


class TestDfeImport(EdiImportCase):
    """Import by access key and from the inbox, with a reader that finds the
    access key written in the file."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env["l10n_br_fiscal_edi.document.import.wizard"]
        cls.DfeDocument = cls.env["l10n_br_fiscal_dfe.document"]

    def setUp(self):
        super().setUp()
        test = self
        document_model = type(self.Document)

        def read(model, name, content):
            text = content.decode()
            if not text.startswith("<xml>"):
                return None
            return test._parsed(text[5:49], file_name=name, content=content)

        def create(model, parsed, company, role):
            return test._create_imported_document(
                company=company, model=model, document_key=parsed.access_key
            )

        for method, replacement in (
            ("_edi_import_read", read),
            ("_edi_import_create", create),
        ):
            patcher = patch.object(document_model, method, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _user(self, login):
        user = self._fiscal_user(login)
        user.email = f"{login}@example.com"
        return user

    def _dfe_document(
        self, key=KEY_1, complete=True, state="1", days=0, fiscal_type="nfe"
    ):
        """An inbox row, with the complete XML or only the summary."""
        dfe_document = self.DfeDocument.create(
            {
                "access_key": key,
                "company_id": self.company.id,
                "fiscal_type": fiscal_type,
                "document_state": state,
                "document_emission_date": fields.Datetime.now() - timedelta(days=days),
            }
        )
        dfe = self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "access_key": key,
                "company_id": self.company.id,
                "fiscal_type": fiscal_type,
                "dfe_document_id": dfe_document.id,
                "document_type_dfe": "complete" if complete else "summary",
            }
        )
        if complete:
            dfe.create_xml_attachment(f"<xml>{key}</xml>".encode())
        return dfe_document

    def _imported(self, key, company=None):
        return self.Document.search(
            [
                ("document_key", "=", key),
                ("company_id", "=", (company or self.company).id),
            ]
        )

    def _by_key(self, key, model=None):
        wizard = (self.Wizard if model is None else model).create({"access_key": key})
        return wizard.action_import()

    def test_the_inbox_opens_the_fiscal_document_of_the_import_of_any_type(self):
        """The document of the import, not its invoice, and with the companies of
        the note in the context, for a note of any type."""
        for fiscal_type in ("nfe", "cte"):
            with self.subTest(fiscal_type=fiscal_type):
                key = KEY_1 if fiscal_type == "nfe" else KEY_2
                row = self._dfe_document(key=key, fiscal_type=fiscal_type)
                row.import_document()
                document = self._imported(key)
                self.assertTrue(document)
                row.invalidate_recordset(["fiscal_document_id"])

                action = row.with_context(
                    allowed_company_ids=[]
                ).action_view_imported_document()

                self.assertEqual(action["res_model"], "l10n_br_fiscal.document")
                self.assertEqual(action["res_id"], document.id)
                self.assertIn(self.company.id, action["context"]["allowed_company_ids"])

    def test_a_repeated_key_opens_the_document_without_asking_the_distribution(self):
        document = self._create_imported_document(document_key=KEY_1)
        company_model = type(self.company)

        with patch.object(
            company_model, "_dfe_search_specific_document", side_effect=AssertionError
        ):
            action = self._by_key(KEY_1)

        self.assertIn("already imported", action["params"]["message"])
        self.assertEqual(action["params"]["next"]["res_id"], document.id)

    @mute_logger("odoo.addons.l10n_br_fiscal_dfe.wizards.document_import_wizard")
    def test_a_connection_failure_with_the_distribution_is_a_clear_message(self):
        company_model = type(self.company)

        with patch.object(
            company_model, "_dfe_search_specific_document", side_effect=OSError("down")
        ), self.assertRaisesRegex(UserError, "could not be reached"):
            self._by_key(KEY_1)

    def test_an_invalid_key_or_one_that_is_not_an_nfe_or_cte_is_refused(self):
        with self.assertRaises(UserError):
            self._by_key("1234")
        key_65 = _nfe_access_key("3520015959431500015765001000000001206277716")
        with self.assertRaisesRegex(UserError, "model 55"):
            self._by_key(key_65)

    def test_the_key_and_files_together_are_refused(self):
        attachment = self.env["ir.attachment"].create({"name": "a.xml", "raw": b"x"})
        wizard = self.Wizard.create(
            {"access_key": KEY_1, "attachment_ids": [Command.set(attachment.ids)]}
        )

        with self.assertRaisesRegex(UserError, "not both"):
            wizard.action_import()

    def test_the_key_of_a_note_with_the_complete_xml_in_the_inbox_imports_it(self):
        dfe_document = self._dfe_document(KEY_1)

        action = self._by_key(KEY_1)

        document = self._imported(KEY_1)
        self.assertEqual(action["res_id"], document.id)
        self.assertIn(KEY_1, "".join(document.message_ids.mapped("body")))
        self.assertIn(
            document.display_name, "".join(dfe_document.message_ids.mapped("body"))
        )

    def test_the_xml_of_the_inbox_is_read_with_bin_size_in_the_context(self):
        dfe_document = self._dfe_document(KEY_1)

        action = dfe_document.with_context(bin_size=True).import_document()

        self.assertEqual(action["res_id"], self._imported(KEY_1).id)

    def test_the_window_reads_the_files_with_bin_size_in_the_context(self):
        attachment = self.env["ir.attachment"].create(
            {"name": "a.xml", "raw": f"<xml>{KEY_2}</xml>".encode()}
        )
        wizard = self.Wizard.with_context(bin_size=True).create(
            {"attachment_ids": [Command.set(attachment.ids)]}
        )

        action = wizard.action_import()

        self.assertEqual(action["res_id"], self._imported(KEY_2).id)

    def test_a_note_cancelled_or_denied_in_the_inbox_is_refused(self):
        for state, text in (("3", "cancelled"), ("2", "denied")):
            dfe_document = self._dfe_document(KEY_1, state=state)
            with self.assertRaisesRegex(UserError, text):
                self._by_key(KEY_1)
            documents, errors, _warnings = self.Document._edi_import_files(
                [("a.xml", f"<xml>{KEY_1}</xml>".encode())]
            )
            self.assertFalse(documents)
            self.assertIn(text, errors[0][1])
            dfe_document.unlink()

    def test_only_the_summary_of_a_type_that_cannot_ask_for_the_xml_asks_for_the_file(
        self,
    ):
        dfe_document = self._dfe_document(KEY_1, complete=False, fiscal_type="cte")

        with self.assertRaisesRegex(UserError, "Upload its XML file"):
            dfe_document.import_document()

    def test_the_xml_that_arrives_creates_the_document_for_who_asked(self):
        user = self._user("dfe_requester")
        dfe_document = self._dfe_document(KEY_1, complete=False)
        dfe_document.import_requested_user_id = user
        dfe = dfe_document.dfe_ids

        dfe.write({"document_type_dfe": "complete"})
        dfe.create_xml_attachment(f"<xml>{KEY_1}</xml>".encode())

        document = self._imported(KEY_1)
        self.assertEqual(document.create_uid, user)
        self.assertFalse(dfe_document.import_requested_user_id)
        self.assertEqual(document.activity_ids.user_id, user)
        self.assertIn(KEY_1, "".join(document.message_ids.mapped("body")))

    @mute_logger("odoo.addons.l10n_br_nfe_dfe.models.dfe_document")
    def test_a_failed_import_of_the_xml_that_arrived_warns_who_asked(self):
        user = self._user("dfe_requester_failed")
        dfe_document = self._dfe_document(KEY_1, complete=False)
        dfe_document.import_requested_user_id = user
        dfe = dfe_document.dfe_ids

        dfe.write({"document_type_dfe": "complete"})
        dfe.create_xml_attachment(b"not a fiscal file")

        self.assertFalse(self._imported(KEY_1))
        self.assertEqual(dfe_document.activity_ids.user_id, user)
        self.assertIn("not a fiscal document", dfe_document.activity_ids.note)

    def test_the_xml_that_arrives_is_read_with_bin_size_in_the_context(self):
        dfe_document = self._dfe_document(KEY_1, complete=False)
        dfe_document.import_requested_user_id = self._user("dfe_requester_size")
        dfe = dfe_document.dfe_ids

        dfe.write({"document_type_dfe": "complete"})
        dfe.with_context(bin_size=True).create_xml_attachment(
            f"<xml>{KEY_1}</xml>".encode()
        )

        self.assertTrue(self._imported(KEY_1))

    def test_a_summary_cancelled_in_the_source_is_not_asked_for(self):
        dfe_document = self._dfe_document(
            KEY_1, complete=False, state="3", fiscal_type="cte"
        )

        with self.assertRaisesRegex(UserError, "cancelled"):
            dfe_document.import_document()

    def test_the_xml_that_arrives_without_a_request_creates_nothing(self):
        dfe_document = self._dfe_document(KEY_1, complete=False)
        dfe = dfe_document.dfe_ids

        dfe.write({"document_type_dfe": "complete"})
        dfe.create_xml_attachment(f"<xml>{KEY_1}</xml>".encode())

        self.assertFalse(self._imported(KEY_1))

    def test_common_fiscal_user_imports_by_key_from_the_inbox_as_the_author(self):
        user = self._user("dfe_fiscal")
        self._dfe_document(KEY_1)
        wizard = self.Wizard.with_user(user).with_context(
            allowed_company_ids=[self.company.id]
        )

        self._by_key(KEY_1, model=wizard)

        self.assertEqual(self._imported(KEY_1).create_uid, user)

    def test_a_fiscal_user_without_email_imports_from_the_inbox(self):
        user = self._fiscal_user("dfe_fiscal_no_email")
        self.assertFalse(user.email)
        dfe_document = self._dfe_document(KEY_1)
        wizard = self.Wizard.with_user(user).with_context(
            allowed_company_ids=[self.company.id]
        )

        self._by_key(KEY_1, model=wizard)

        document = self._imported(KEY_1)
        self.assertEqual(document.create_uid, user)
        self.assertIn(KEY_1, "".join(document.message_ids.mapped("body")))
        self.assertIn(
            document.display_name, "".join(dfe_document.message_ids.mapped("body"))
        )

    def test_common_fiscal_user_asks_the_distribution_by_key(self):
        user = self._user("dfe_fiscal_query")
        wizard = self.Wizard.with_user(user).with_context(
            allowed_company_ids=[self.company.id]
        )
        test = self

        def search(company, fiscal_type, access_key=None, nsu=None):
            test.assertTrue(company.env.su)
            test._dfe_document(access_key)

        with patch.object(type(self.company), "_dfe_search_specific_document", search):
            self._by_key(KEY_1, model=wizard)

        self.assertEqual(self._imported(KEY_1).create_uid, user)

    def test_the_window_has_the_key_and_the_files(self):
        arch = self.Wizard.get_view(view_type="form")["arch"]

        self.assertIn('name="access_key"', arch)
        self.assertIn('name="attachment_ids"', arch)

    def test_the_form_of_the_inbox_has_the_history(self):
        arch = self.DfeDocument.get_view(view_type="form")["arch"]

        self.assertIn("oe_chatter", arch)
