# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import io
import threading
import zipfile
from contextlib import closing
from unittest.mock import patch

from erpbrasil.base.fiscal.cnpj_cpf import formata
from psycopg2 import OperationalError
from psycopg2.errorcodes import SERIALIZATION_FAILURE

from odoo import SUPERUSER_ID, _, api
from odoo.exceptions import AccessError, UserError
from odoo.sql_db import db_connect

from ..tools import EDI_IMPORT_DEMO, EDI_IMPORT_NO_CREATE, EdiPartnerData
from .common import KEY_1, KEY_2, KEY_3, EdiImportCase


def _zip(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files:
            archive.writestr(name, content)
    return buffer.getvalue()


class TestDocumentImport(EdiImportCase):
    """The service of import, with a reader that finds what the test tells it to."""

    def _import(self, files, parsed=(), model=None, **create_values):
        """Run ``_edi_import_files`` with a reader that recognizes the parsed files
        by their name and a creator that builds the draft document."""
        by_name = {parsed_file.file_name: parsed_file for parsed_file in parsed}
        test = self
        created = []

        def read(model_, name, content):
            return by_name.get(name)

        def create(model_, parsed_file, company, role):
            self.create_context = dict(model_.env.context)
            created.append(model_.env.context.get(EDI_IMPORT_NO_CREATE))
            return test._create_imported_document(
                company=company,
                model=model_,
                document_key=parsed_file.access_key,
                **create_values,
            )

        document_model = type(self.Document)
        with patch.object(document_model, "_edi_import_read", read), patch.object(
            document_model, "_edi_import_create", create
        ):
            result = (self.Document if model is None else model)._edi_import_files(
                files
            )
        self.create_contexts = created
        return result

    def test_a_file_is_imported_and_the_creation_never_creates_registries(self):
        parsed = self._parsed(KEY_1)
        documents, errors, warnings = self._import([(parsed.file_name, b"x")], [parsed])
        self.assertEqual((len(documents), errors, warnings), (1, [], []))
        self.assertEqual(self.create_contexts, [True])
        self.assertTrue(documents.imported_document)
        self.assertEqual(documents.document_key, KEY_1)

    def _another_transaction_can_lock(self, company, key):
        """Whether a transaction of its own could take the lock of the note now."""
        connection = db_connect(self.env.cr.dbname)
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                "SELECT pg_try_advisory_xact_lock(%s, hashtext(%s))", (company.id, key)
            )
            free = cursor.fetchone()[0]
            cursor.rollback()
        return free

    def test_the_import_of_a_note_holds_its_lock_until_the_transaction_ends(self):
        """Two imports of the same note at once must end in one document: the second
        waits for the first, so it finds the document. Another transaction cannot take
        the lock of the note of that company, but can take the one of another note and
        the one of the same note in another company."""
        parsed = self._parsed(KEY_1)
        self.assertTrue(self._another_transaction_can_lock(self.company, KEY_1))
        self._import([(parsed.file_name, b"x")], [parsed])
        self.assertFalse(self._another_transaction_can_lock(self.company, KEY_1))
        self.assertTrue(self._another_transaction_can_lock(self.company, KEY_2))
        self.assertTrue(self._another_transaction_can_lock(self.other_company, KEY_1))

    def _commit_document_elsewhere(self, key, lock=False):
        """Create, in a connection of its own, an imported document with the key, and
        commit it, as another transaction that imported the same note does. With
        ``lock``, the lock of the note is taken first and the commit is left to the
        caller. The document is deleted when the test ends."""
        cursor = db_connect(self.env.cr.dbname).cursor()
        env = api.Environment(cursor, SUPERUSER_ID, {})
        company = env["res.company"].browse(self.company.id)
        if lock:
            cursor.execute(
                "SELECT pg_advisory_xact_lock(%s, hashtext(%s))", (company.id, key)
            )
        document = (
            env["l10n_br_fiscal.document"]
            .with_company(company)
            .create(
                {
                    "company_id": company.id,
                    "document_type_id": env.ref("l10n_br_fiscal.document_55").id,
                    "imported_document": True,
                    "issuer": "partner",
                    "partner_id": env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                    "document_key": key,
                    "document_number": "99999",
                    "document_serie": "9",
                }
            )
        )

        def clean():
            with closing(db_connect(self.env.cr.dbname).cursor()) as other:
                other.execute(
                    "DELETE FROM l10n_br_fiscal_document WHERE document_key = %s",
                    (key,),
                )
                other.commit()

        self.addCleanup(clean)
        if not lock:
            cursor.commit()
            cursor.close()
        return cursor, document

    def _import_expecting_a_retry(self, key):
        parsed = self._parsed(key)
        with self.assertRaises(OperationalError) as caught:
            self._import([(parsed.file_name, b"x")], [parsed])
        self.assertEqual(caught.exception.pgcode, SERIALIZATION_FAILURE)

    def test_a_note_committed_after_the_snapshot_asks_the_call_to_run_again(self):
        """Nobody holds the lock when it is asked for, but another transaction
        committed the same note after the snapshot of this one: the search does not
        see it, and a second document must not be born."""
        self.Document.search_count([])  # the snapshot of this transaction
        self._commit_document_elsewhere(KEY_1)
        self._import_expecting_a_retry(KEY_1)
        self.assertFalse(self.Document.search([("document_key", "=", KEY_1)]))

    def test_a_note_committed_while_waiting_for_the_lock_asks_the_call_to_run_again(
        self,
    ):
        """The other transaction holds the lock of the note and commits the document
        while this one waits for it."""
        self.Document.search_count([])
        cursor, _document = self._commit_document_elsewhere(KEY_2, lock=True)
        release = threading.Timer(1.0, cursor.commit)
        release.start()
        try:
            self._import_expecting_a_retry(KEY_2)
        finally:
            release.join()
            cursor.close()

    def test_a_note_that_this_transaction_deleted_is_not_a_concurrent_import(self):
        """The document was committed before the snapshot of this transaction, which
        deleted it: the other connection still sees the row, but the row is not newer
        than the snapshot, so there is no one to wait for, and the note is imported
        again (the inbox tests of a CT-e delete the demo one and import its file)."""
        self._commit_document_elsewhere(KEY_2)
        with closing(db_connect(self.env.cr.dbname).cursor()) as cursor:
            cursor.execute("SELECT txid_current_snapshot()::text")
            after_the_commit = cursor.fetchone()[0]
        parsed = self._parsed(KEY_2)
        with patch.object(
            type(self.Document),
            "_edi_import_snapshot",
            lambda doc: doc._edi_import_parse_snapshot(after_the_commit),
        ):
            documents, errors, _warnings = self._import(
                [(parsed.file_name, b"x")], [parsed]
            )
        self.assertEqual((len(documents), errors), (1, []))

    def test_the_row_of_a_transaction_that_the_snapshot_does_not_see_is_newer(self):
        born_after = self.Document._edi_import_born_after
        snapshot = self.Document._edi_import_parse_snapshot("100:110:103,105")
        self.assertFalse(born_after(snapshot, 99))
        self.assertFalse(born_after(snapshot, 104))
        self.assertTrue(born_after(snapshot, 103))
        self.assertTrue(born_after(snapshot, 110))
        self.assertTrue(born_after(snapshot, 4000))

    def test_a_table_locked_by_the_transaction_does_not_hang_the_import(self):
        """An installation that imports the demo data holds locks on the table, and
        the connection that looks for a note committed elsewhere would wait for them
        for ever: it gives up after a short time and the import goes on."""
        self.env.cr.execute(
            "LOCK TABLE l10n_br_fiscal_document IN ACCESS EXCLUSIVE MODE"
        )
        parsed = self._parsed(KEY_3)
        documents, errors, _warnings = self._import(
            [(parsed.file_name, b"x")], [parsed]
        )
        self.assertEqual((len(documents), errors), (1, []))

    def test_the_demo_data_does_not_look_for_a_note_committed_elsewhere(self):
        """The demo is imported while the module is installed: no other connection
        is opened to look for the note, and the import does not wait for the locks."""
        self.env.cr.execute(
            "LOCK TABLE l10n_br_fiscal_document IN ACCESS EXCLUSIVE MODE"
        )
        parsed = self._parsed(KEY_3)
        with patch.object(
            type(self.Document),
            "_edi_import_snapshot",
            side_effect=AssertionError("looked for the note"),
        ):
            documents, errors, _warnings = self._import(
                [(parsed.file_name, b"x")],
                [parsed],
                model=self.Document.with_context(**{EDI_IMPORT_DEMO: True}),
            )
        self.assertEqual((len(documents), errors), (1, []))

    def test_a_serialization_failure_of_the_database_is_not_an_error_of_the_file(self):
        class Serialization(OperationalError):
            pgcode = SERIALIZATION_FAILURE

        parsed = self._parsed(KEY_1)

        def fail(*args):
            raise Serialization("could not serialize access")

        with (
            patch.object(type(self.Document), "_edi_import_create", fail),
            patch.object(type(self.Document), "_edi_import_read", lambda *args: parsed),
            self.assertRaises(OperationalError),
        ):
            self.Document._edi_import_files([(parsed.file_name, b"x")])

    def test_another_error_of_the_database_is_reported_as_unexpected(self):
        parsed = self._parsed(KEY_1)

        def fail(*args):
            raise OperationalError("another problem")

        with (
            patch.object(type(self.Document), "_edi_import_create", fail),
            patch.object(type(self.Document), "_edi_import_read", lambda *args: parsed),
        ):
            _documents, errors, _warnings = self.Document._edi_import_files(
                [(parsed.file_name, b"x")]
            )
        self.assertEqual([name for name, _message in errors], [parsed.file_name])

    def test_a_reader_that_creates_another_type_of_document_is_refused(self):
        parsed = self._parsed(KEY_1)
        cte = self.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", "57")], limit=1
        )
        _documents, errors = self._import_with_document_type(parsed, cte)
        self.assertEqual(len(errors), 1)
        self.assertIn("type 57", errors[0][1])

    def _import_with_document_type(self, parsed, document_type):
        by_name = {parsed.file_name: parsed}
        test = self

        def create(model_, parsed_file, company, role):
            return test._create_imported_document(
                company=company,
                model=model_,
                document_key=parsed_file.access_key,
                document_type_id=document_type.id,
            )

        with (
            patch.object(
                type(self.Document), "_edi_import_read", lambda m, n, c: by_name.get(n)
            ),
            patch.object(type(self.Document), "_edi_import_create", create),
        ):
            documents, errors, _warnings = self.Document._edi_import_files(
                [(parsed.file_name, b"x")]
            )
        return documents, errors

    def test_the_demo_files_of_a_module_are_imported_by_the_service(self):
        document = self._create_imported_document(document_key=KEY_1)
        calls = []

        def service(model, files, **kwargs):
            calls.append(files)
            return document, [], []

        with patch.object(type(self.Document), "_edi_import_files", service):
            documents = self.Document._edi_import_demo_files(
                "l10n_br_fiscal_edi", ["__manifest__.py"]
            )
        self.assertEqual(documents, document)
        self.assertEqual([name for name, _content in calls[0]], ["__manifest__.py"])
        self.assertIn(b"Common EDI fiscal features", calls[0][0][1])

    def test_a_demo_file_that_fails_stops_the_installation(self):
        with self.assertRaises(UserError):
            self.Document._edi_import_demo_files(
                "l10n_br_fiscal_edi", ["__manifest__.py"]
            )

    def test_the_same_note_twice_opens_the_same_document_with_a_warning(self):
        parsed = self._parsed(KEY_1)
        files = [(parsed.file_name, b"x"), (parsed.file_name, b"x")]
        documents, errors, warnings = self._import(files, [parsed])
        self.assertEqual(len(documents), 1)
        self.assertFalse(errors)
        self.assertEqual([name for name, _msg in warnings], [parsed.file_name])
        self.assertEqual(self.Document.search_count([("document_key", "=", KEY_1)]), 1)

    def test_an_error_in_one_file_does_not_drop_the_batch(self):
        good, other = self._parsed(KEY_1), self._parsed(KEY_2)
        files = [
            (good.file_name, b"x"),
            ("garbage.xml", b"not a fiscal file"),
            (other.file_name, b"x"),
        ]
        documents, errors, _warnings = self._import(files, [good, other])
        self.assertEqual(len(documents), 2)
        self.assertEqual([name for name, _msg in errors], ["garbage.xml"])
        self.assertIn("not a fiscal document", errors[0][1])

    def test_a_zip_stands_for_the_files_it_holds(self):
        good, other = self._parsed(KEY_1), self._parsed(KEY_2)
        archive = _zip(
            [
                ("dir/", b""),
                ("__MACOSX/._" + good.file_name, b"metadata"),
                (good.file_name, b"x"),
                (other.file_name, b"x"),
            ]
        )
        names = [
            name
            for name, _content in self.Document._edi_import_expand(
                [("all.zip", archive)]
            )
        ]
        self.assertEqual(
            names, [f"all.zip/{good.file_name}", f"all.zip/{other.file_name}"]
        )

    def test_zip_with_two_notes_and_an_invalid_file(self):
        good, other = self._parsed(KEY_1), self._parsed(KEY_2)
        archive = _zip(
            [(good.file_name, b"x"), ("bad.xml", b"x"), (other.file_name, b"x")]
        )
        by_zip_name = [
            self._parsed(KEY_1, file_name=f"all.zip/{good.file_name}"),
            self._parsed(KEY_2, file_name=f"all.zip/{other.file_name}"),
        ]
        documents, errors, _warnings = self._import([("all.zip", archive)], by_zip_name)
        self.assertEqual(len(documents), 2)
        self.assertEqual([name for name, _msg in errors], ["all.zip/bad.xml"])

    def test_an_unexpected_error_is_reported_without_the_raw_message(self):
        parsed = self._parsed(KEY_1)
        with patch.object(
            type(self.Document), "_edi_import_read", side_effect=ValueError("secret")
        ):
            documents, errors, _warnings = self.Document._edi_import_files(
                [(parsed.file_name, b"x")]
            )
        self.assertFalse(documents)
        self.assertNotIn("secret", errors[0][1])
        self.assertIn("unexpected error", errors[0][1])

    def test_a_cancelled_or_denied_note_is_refused(self):
        for status, text in (("cancelled", "cancelled"), ("denied", "denied")):
            parsed = self._parsed(KEY_1, status=status)
            documents, errors, _warnings = self._import(
                [(parsed.file_name, b"x")], [parsed]
            )
            self.assertFalse(documents)
            self.assertIn(text, errors[0][1])
        self.assertFalse(self.Document.search([("document_key", "=", KEY_1)]))

    def test_a_company_outside_the_switcher_is_refused_before_creating(self):
        parsed = self._parsed(KEY_1, company=self.other_company)
        model = self.Document.with_context(allowed_company_ids=self.company.ids)
        documents, errors, _warnings = self._import(
            [(parsed.file_name, b"x")], [parsed], model=model
        )
        self.assertFalse(documents)
        self.assertIn("not selected in the company switcher", errors[0][1])
        self.assertEqual(self.create_contexts, [])
        self.assertFalse(self.Document.search([("document_key", "=", KEY_1)]))

    def test_a_company_the_user_cannot_access_is_refused(self):
        user = self._fiscal_user("fiscal_user_company")
        parsed = self._parsed(KEY_1, company=self.other_company)
        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.company.ids
        )
        documents, errors, _warnings = self._import(
            [(parsed.file_name, b"x")], [parsed], model=model
        )
        self.assertFalse(documents)
        self.assertIn("no access to the company", errors[0][1])
        self.assertEqual(self.create_contexts, [])

    def test_a_user_of_another_company_gets_a_clear_refusal_not_an_access_error(self):
        """The file is for a company that the user does not have: the answer says so
        and which CNPJ the file is for, instead of the raw access error of Odoo, and
        it never needs to read the name of a company the user cannot see."""
        user = self._fiscal_user(
            "fiscal_user_only_company_2", companies=self.other_company
        )
        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.other_company.ids
        )
        parsed = self._parsed(KEY_1)
        with self.assertRaises(UserError) as error:
            model._edi_import_company(parsed)
        message = str(error.exception)
        self.assertIn("no access to the company with the CNPJ", message)
        self.assertIn(self._cnpj(self.company), message)
        self.assertNotIn(self.company.name, message)

    def _cnpj(self, company):
        return formata(company.partner_id.cnpj_cpf_stripped)

    def test_the_company_is_searched_in_the_order_of_the_roles(self):
        parsed = self._parsed(
            KEY_1,
            company_vats=(
                ("taker", "00000000000000"),
                ("issuer", self.company.partner_id.cnpj_cpf_stripped),
            ),
        )
        company, role = self.Document._edi_import_company(parsed)
        self.assertEqual((company, role), (self.company, "issuer"))
        with self.assertRaises(UserError):
            self.Document._edi_import_company(
                self._parsed(KEY_1, company_vats=(("recipient", "00000000000000"),))
            )

    def test_the_role_of_the_company_tells_the_direction_of_the_document(self):
        incoming = self._create_imported_document()
        incoming._edi_import_after_create(self._parsed(KEY_1), "recipient")
        self.assertEqual(incoming.issuer, "partner")
        self.assertEqual(incoming.fiscal_operation_type, "in")
        own = self._create_imported_document()
        own._edi_import_after_create(self._parsed(KEY_2), "issuer")
        self.assertEqual(own.issuer, "company")
        self.assertEqual(own.fiscal_operation_type, "out")
        self.assertTrue(own.imported_document)

    def test_the_file_is_kept_and_the_partners_it_created_are_recorded(self):
        document = self._create_imported_document()
        last = self.env["res.partner"].search([], order="id desc", limit=1)
        created = self.env["res.partner"].create({"name": "Born from the file"})
        document.with_context(
            edi_import_last_partner_id=last.id
        )._edi_import_after_create(self._parsed(KEY_1), "recipient")
        self.assertEqual(
            document.original_xml_file_id.raw, f"<xml>{KEY_1}</xml>".encode()
        )
        self.assertIn(created.display_name, document.message_ids[0].body)

    def test_a_user_with_no_email_imports_and_the_partners_are_recorded(self):
        """The history of the import is a note that is sent to nobody, so a fiscal
        user without an email address can import."""
        user = self._fiscal_user("fiscal_user_no_email")
        user.partner_id.email = False
        self.assertFalse(user.partner_id.email)
        document = self._create_imported_document()
        last = self.env["res.partner"].search([], order="id desc", limit=1)
        created = (
            self.env["res.partner"]
            .with_user(user)
            .sudo()
            .create({"name": "Born from the file of a user"})
        )
        self.assertEqual(created.create_uid, user)
        document.with_user(user).with_context(
            allowed_company_ids=self.company.ids, edi_import_last_partner_id=last.id
        )._edi_import_after_create(self._parsed(KEY_1), "recipient")
        self.assertIn(created.display_name, document.message_ids[0].body)

    def _check_partners(self, document, data, partner=None, **context):
        """Run the comparison with a reader that declares ``data`` for the partner."""
        partner = partner or document.partner_id
        with patch.object(
            type(self.Document),
            "_edi_import_partner_data",
            lambda doc, parsed: [(partner, data)],
        ):
            document.with_context(**context)._edi_import_check_partners(
                self._parsed(KEY_1)
            )

    def test_data_of_the_file_that_differ_from_the_registry_are_listed(self):
        """Name and address of the file against the registry: the document says what
        differs, with the value of each side, and the registry is not touched."""
        self.supplier.write(
            {
                "legal_name": "Fornecedor Alfa Ltda",
                "street_name": "Avenida Afonso Pena",
                "street_number": "100",
                "zip": "30130-010",
            }
        )
        document = self._create_imported_document()
        data = EdiPartnerData(
            role="issuer",
            vat="59594315000157",
            name="FORNECEDOR BETA LTDA",
            street="AVENIDA AFONSO PENA",
            street_number="200",
            zip_code="30130010",
        )
        self._check_partners(document, data)
        warning = document.import_partner_warning
        self.assertIn("FORNECEDOR BETA LTDA", warning)
        self.assertIn("Fornecedor Alfa Ltda", warning)
        self.assertIn('"200"', warning)
        self.assertIn('"100"', warning)
        self.assertNotIn("ZIP code", warning)
        self.assertNotIn("Street", warning)
        self.assertEqual(document.import_warning.count("FORNECEDOR BETA"), 1)
        self.assertEqual(self.supplier.legal_name, "Fornecedor Alfa Ltda")
        self.assertEqual(self.supplier.street_number, "100")
        self.assertIn("differ from the registry", document.message_ids[0].body)

    def test_the_warning_is_the_picture_of_a_day_and_checking_again_updates_it(self):
        """A registry corrected after the import does not change the warning by itself:
        it says when it was compared, and the button compares again and clears it."""
        self.supplier.write({"legal_name": "Fornecedor Alfa Ltda"})
        document = self._create_imported_document()
        data = EdiPartnerData(role="issuer", vat="59594315000157", name="Beta Ltda")
        self._check_partners(document, data)
        self.assertIn("Beta Ltda", document.import_partner_warning)
        self.assertTrue(document.import_partner_checked)
        self.assertIn("as compared with the registry on", document.import_warning)
        # the registry is corrected: nothing changes until somebody checks again
        self.supplier.write({"legal_name": "Beta Ltda"})
        document.invalidate_recordset()
        self.assertIn("Beta Ltda", document.import_partner_warning)
        document.original_xml_file_id = self.env["ir.attachment"].create(
            {"name": "a.xml", "raw": b"<a/>"}
        )
        model = type(self.Document)
        with patch.object(
            model, "_edi_import_read", lambda doc, name, content: self._parsed(KEY_1)
        ), patch.object(
            model,
            "_edi_import_partner_data",
            lambda doc, parsed: [(doc.partner_id, data)],
        ):
            document.action_import_check_partners_again()
        self.assertFalse(document.import_partner_warning)
        self.assertNotIn(
            "as compared with the registry on", document.import_warning or ""
        )
        # a document whose file is gone says so
        document.original_xml_file_id = False
        with self.assertRaises(UserError):
            document.action_import_check_partners_again()

    def test_the_same_data_written_differently_is_not_reported(self):
        self.supplier.write(
            {
                "legal_name": "Fornecedor Alfa Ltda.",
                "street_name": "Avenida Afonso Pena",
                "district": "Funcionarios",
                "zip": "30130-010",
            }
        )
        document = self._create_imported_document()
        data = EdiPartnerData(
            role="issuer",
            vat="59594315000157",
            name="FORNECEDOR ALFA LTDA",
            street="Avenida  Afonso-Pena",
            district="FUNCIONÁRIOS",
            zip_code="30130010",
        )
        self._check_partners(document, data)
        self.assertFalse(document.import_partner_warning)

    def test_a_partner_matched_by_name_because_the_file_has_no_vat_is_reported(self):
        document = self._create_imported_document()
        self._check_partners(document, EdiPartnerData(role="issuer", name="Whoever"))
        self.assertIn("matched by name", document.import_partner_warning)

    def test_the_company_itself_is_not_compared_with_the_file(self):
        document = self._create_imported_document()
        own = self.company.partner_id
        data = EdiPartnerData(role="issuer", vat="1", name="Another name entirely")
        self._check_partners(document, data, partner=own)
        self.assertFalse(document.import_partner_warning)

    def test_viewing_the_pdf_again_does_not_regenerate_it(self):
        """The imported document has only the XML it came with, and an issued one has
        the authorization file: either way the second click opens the same PDF."""
        for imported in (True, False):
            document = self._create_imported_document(imported_document=imported)
            xml = self.env["ir.attachment"].create({"name": "a.xml", "raw": b"<a/>"})
            if imported:
                document.original_xml_file_id = xml
            else:
                serie = self.env["l10n_br_fiscal.document.serie"].create(
                    {
                        "code": "8",
                        "name": "Series of the pdf",
                        "company_id": self.company.id,
                        "document_type_id": document.document_type_id.id,
                    }
                )
                document.authorization_event_id = self.env[
                    "l10n_br_fiscal.event"
                ].create(
                    {
                        "type": "0",
                        "company_id": self.company.id,
                        "document_id": document.id,
                        "document_type_id": document.document_type_id.id,
                        "document_serie_id": serie.id,
                        "document_number": "1",
                        "origin": "Test",
                        "file_response_id": xml.id,
                    }
                )
            calls = []
            record = calls.append

            def make_pdf(doc, record=record):
                record(1)
                doc.file_report_id = self.env["ir.attachment"].create(
                    {"name": "a.pdf", "raw": b"pdf"}
                )

            with patch.object(type(self.Document), "make_pdf", make_pdf):
                document.view_pdf()
                first = document.file_report_id
                document.view_pdf()
            self.assertEqual(document.file_report_id, first)
            self.assertEqual(len(calls), 1, f"imported={imported}")

    def test_a_partner_created_by_the_import_is_not_compared(self):
        document = self._create_imported_document()
        data = EdiPartnerData(role="issuer", vat="1", name="Other name")
        self._check_partners(
            document, data, edi_import_last_partner_id=document.partner_id.id - 1
        )
        self.assertFalse(document.import_partner_warning)

    def test_a_reader_with_no_partner_data_reports_nothing(self):
        document = self._create_imported_document()
        document._edi_import_check_partners(self._parsed(KEY_1))
        self.assertFalse(document.import_partner_warning)

    def _own_document(self, lines, direction="out", **values):
        """Imported document, issued by the company when ``direction`` is out, whose
        lines declare the code of their product."""
        document = self._create_imported_document(
            issuer="company" if direction == "out" else "partner",
            fiscal_operation_id=False,
            lines=lines,
            **values,
        )
        document.fiscal_operation_type = direction
        return document

    def _declared_codes(self):
        return patch.object(
            type(self.env["l10n_br_fiscal.document.line"]),
            "_get_partner_product_code",
            lambda line: line.name.split()[0],
        )

    def test_a_line_of_a_document_the_company_issued_resolves_by_its_own_code(self):
        """In a document the company issued the code of the file is the internal
        code: the line enters resolved. In a document received it is only a
        suggestion, as before."""
        product = self.env["product.product"].create(
            {"name": "Own product", "default_code": "OWN-1"}
        )
        for direction, state in (("out", "resolved"), ("in", "matched")):
            document = self._own_document(
                [{"name": "OWN-1 sold item"}], direction=direction
            )
            with self._declared_codes():
                document._edi_import_suggest()
            line = document.fiscal_line_ids
            if direction == "out":
                self.assertEqual(line.product_id, product)
                self.assertEqual(line.import_state, state)
                self.assertFalse(line.import_supplierinfo_id)
            else:
                self.assertNotEqual(line.import_state, "resolved")

    def test_a_declared_unit_that_is_not_confirmed_blocks_the_own_product(self):
        product = self.env["product.product"].create(
            {"name": "Own product", "default_code": "OWN-2"}
        )
        document = self._own_document(
            [{"name": "OWN-2 sold item", "partner_uom_code": "ZZZ"}]
        )
        with self._declared_codes():
            document._edi_import_suggest()
        line = document.fiscal_line_ids
        self.assertEqual(line.product_id, product)
        self.assertEqual(line.import_state, "pending")

    def test_the_missing_products_are_created_by_an_explicit_action(self):
        ncm = self.env["l10n_br_fiscal.ncm"].create(
            {"name": "NCM of the file", "code": "9999.99.99"}
        )
        document = self._own_document(
            [
                {"name": "OWN-3 first", "ncm_id": ncm.id, "icms_origin": "1"},
                {"name": "OWN-3 again"},
                {"name": "OWN-4 known", "product_id": False},
                {"name": "OWN-5 odd unit", "partner_uom_code": "ZZZ"},
            ]
        )
        product_model = self.env["product.product"]
        with self._declared_codes():
            before = product_model.search_count([])
            # the import never creates a product
            document._edi_import_suggest()
            self.assertEqual(
                product_model.search([("default_code", "=", "OWN-3")]).ids, []
            )
            # a product with a code of the file appears before the action is run
            existing = product_model.create(
                {"name": "Already there", "default_code": "OWN-4"}
            )
            before += 1
            self.assertTrue(document.import_missing_products)
            action = document.action_import_create_products()
            # only the line with an unknown unit is left, and it cannot be created
            self.assertFalse(document.import_missing_products)
            created = product_model.search([("default_code", "=", "OWN-3")])
            self.assertEqual(len(created), 1)
            self.assertEqual(created.name, "OWN-3 first")
            self.assertEqual(created.ncm_id, ncm)
            self.assertEqual(created.icms_origin, "1")
            self.assertEqual(created.uom_id, self.uom_unit)
            self.assertEqual(product_model.search_count([]), before + 1)
            lines = document.fiscal_line_ids
            self.assertEqual(lines[0].product_id, created)
            self.assertEqual(lines[1].product_id, created)
            self.assertEqual(lines[2].product_id, existing)
            self.assertEqual(lines.mapped("import_state")[:3], ["resolved"] * 3)
            # the unit that matched nothing blocks: no product, no unit created
            self.assertFalse(lines[3].product_id)
            self.assertFalse(product_model.search([("default_code", "=", "OWN-5")]))
            self.assertEqual(action["tag"], "display_notification")
            self.assertIn("Products created by", document.message_ids[0].body)
            self.assertIn("OWN-3", document.message_ids[0].body)
            # the second time creates nothing
            document.action_import_create_products()
            self.assertEqual(product_model.search_count([]), before + 1)

    def test_products_are_not_created_for_a_document_received(self):
        document = self._own_document([{"name": "REC-1 item"}], direction="in")
        with self.assertRaises(UserError):
            document.action_import_create_products()

    def test_a_user_who_cannot_create_products_cannot_run_the_action(self):
        user = self._fiscal_user("fiscal_user_no_product")
        document = self._own_document([{"name": "NOP-1 item"}])
        model = document.with_user(user).with_context(
            allowed_company_ids=self.company.ids
        )
        self.assertFalse(model.import_can_create_products)
        with self.assertRaises(UserError):
            model.action_import_create_products()
        self.assertFalse(
            self.env["product.product"].search([("default_code", "=", "NOP-1")])
        )

    def test_a_reader_that_is_not_installed_refuses_the_file(self):
        parsed = self._parsed(KEY_1, reader="cte")
        with patch.object(
            type(self.Document), "_edi_import_read", lambda *args: parsed
        ):
            documents, errors, _warnings = self.Document._edi_import_files(
                [(parsed.file_name, b"x")]
            )
        self.assertFalse(documents)
        self.assertIn("no importer", errors[0][1])

    def test_the_suggestion_does_not_touch_the_values_of_the_file(self):
        document = self._create_imported_document(
            fiscal_operation_id=False,
            lines=[
                {
                    "quantity": 3.0,
                    "price_unit": 7.5,
                    "partner_cfop_id": self.env.ref("l10n_br_fiscal.cfop_5102").id,
                }
            ],
        )
        document._edi_import_after_create(self._parsed(KEY_1), "recipient")
        document._edi_import_suggest()
        line = document.fiscal_line_ids
        self.assertTrue(document.fiscal_operation_id)
        self.assertEqual(document.fiscal_operation_type, "in")
        self.assertEqual(line.fiscal_operation_id, document.fiscal_operation_id)
        self.assertEqual((line.quantity, line.price_unit), (3.0, 7.5))
        self.assertEqual(line.partner_cfop_id.code, "5102")

    def test_a_document_with_no_matching_operation_keeps_its_direction(self):
        """Nothing matches the CFOP: the operation stays empty, and the direction
        that the import gave the document is not recomputed away."""
        cfop = self.env.ref("l10n_br_fiscal.cfop_6102")
        for role, direction in (("recipient", "in"), ("issuer", "out")):
            document = self._create_imported_document(
                fiscal_operation_id=False,
                lines=[{"partner_cfop_id": cfop.id}],
            )
            document._edi_import_after_create(self._parsed(KEY_1), role)
            with patch.object(
                type(self.env["l10n_br_fiscal.operation.line"]),
                "_find_by_issuer_cfop",
                lambda *args, **kwargs: self.env["l10n_br_fiscal.operation.line"],
            ):
                document._edi_import_suggest()
            self.assertFalse(document.fiscal_operation_id)
            self.assertEqual(document.fiscal_operation_type, direction)

    def test_a_document_the_company_issued_gets_its_operation_as_an_output(self):
        """A document the company issued in another system is reviewed like any
        other: its operation is the one of its own CFOP, in the direction of out."""
        operation = self.env["l10n_br_fiscal.operation"].create(
            {
                "code": "TST-OUT",
                "name": "Own sale (test)",
                "fiscal_operation_type": "out",
                "fiscal_type": "sale",
            }
        )
        self.env["l10n_br_fiscal.operation.line"].create(
            {
                "fiscal_operation_id": operation.id,
                "name": "Own sale (test)",
                "cfop_internal_id": self.env.ref("l10n_br_fiscal.cfop_5102").id,
            }
        )
        operation.action_approve()
        document = self._create_imported_document(
            fiscal_operation_id=False,
            lines=[{"partner_cfop_id": self.env.ref("l10n_br_fiscal.cfop_5102").id}],
        )
        document._edi_import_after_create(self._parsed(KEY_1), "issuer")
        document.partner_operation_name = operation.name
        document._edi_import_suggest()
        self.assertEqual(document.fiscal_operation_id, operation)
        self.assertEqual(document.fiscal_operation_type, "out")
        self.assertEqual(document.fiscal_line_ids.fiscal_operation_id, operation)
        self.assertEqual(document.fiscal_line_ids.import_state, "pending")

    def test_the_nature_declared_by_the_file_breaks_a_tie_in_the_suggestion(self):
        """Two operations answer the CFOP of the line: the one named like the nature
        that the reader stored on the document is suggested."""
        operation = self.env["l10n_br_fiscal.operation"].create(
            {
                "code": "TST-NAT",
                "name": "Nature declared by the issuer (test)",
                "fiscal_operation_type": "in",
                "fiscal_type": "purchase",
            }
        )
        self.env["l10n_br_fiscal.operation.line"].create(
            {
                "fiscal_operation_id": operation.id,
                "name": "Nature declared by the issuer (test)",
                "cfop_internal_id": self.env.ref("l10n_br_fiscal.cfop_1102").id,
            }
        )
        operation.action_approve()
        cfop = self.env.ref("l10n_br_fiscal.cfop_5102")
        for declared, expected in ((operation.name, operation), (False, False)):
            document = self._create_imported_document(
                fiscal_operation_id=False,
                partner_operation_name=declared,
                lines=[{"partner_cfop_id": cfop.id}],
            )
            document._edi_import_after_create(self._parsed(KEY_1), "recipient")
            document._edi_import_suggest()
            if expected:
                self.assertEqual(document.fiscal_operation_id, expected)
                self.assertEqual(document.fiscal_line_ids.fiscal_operation_id, expected)
            else:
                self.assertNotEqual(document.fiscal_operation_id, operation)

    def test_the_suggestion_can_run_again_without_undoing_a_decision(self):
        product = self.env["product.product"].create({"name": "Chosen by a person"})
        document = self._create_imported_document()
        line = document.fiscal_line_ids
        line.product_id = product
        line._apply_import_depara(uom=self.uom_unit)
        self.assertEqual(line.import_state, "resolved")
        document._edi_import_suggest()
        document._edi_import_suggest()
        self.assertEqual(line.import_state, "resolved")
        self.assertEqual(line.product_id, product)

    def test_a_product_mapped_for_the_same_supplier_enters_resolved(self):
        product = self.env["product.product"].create({"name": "Mapped product"})
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.supplier.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_id": product.id,
                "product_code": "SUP-1",
                "price": 1.0,
            }
        )
        with patch.object(
            type(self.env["l10n_br_fiscal.document.line"]),
            "_get_partner_product_code",
            lambda line: "SUP-1",
        ):
            document = self._create_imported_document()
            document._edi_import_suggest()
        line = document.fiscal_line_ids
        self.assertEqual(line.product_id, product)
        self.assertEqual(line.import_state, "resolved")

    def test_unknown_unit_with_a_product_mapped_by_the_supplier_awaits_review(self):
        """The supplier mapped the product, but the unit it declares now matches
        nothing: the product is set and the line still waits for a person."""
        product = self.env["product.product"].create({"name": "Mapped product"})
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.supplier.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_id": product.id,
                "product_code": "SUP-1",
                "price": 1.0,
            }
        )
        with patch.object(
            type(self.env["l10n_br_fiscal.document.line"]),
            "_get_partner_product_code",
            lambda line: "SUP-1",
        ):
            document = self._create_imported_document(
                lines=[{"partner_uom_code": "ZZZ"}]
            )
            document._edi_import_suggest()
        line = document.fiscal_line_ids
        self.assertEqual(line.product_id, product)
        self.assertEqual(line.import_state, "pending")

    def test_the_review_of_a_document_the_company_issued_learns_no_supplier(self):
        product = self.env["product.product"].create({"name": "Sold product"})
        customer = self.env["res.partner"].create({"name": "Customer of the sale"})
        for direction, learned in (("out", 0), ("in", 1)):
            document = self._create_imported_document(
                partner=customer,
                fiscal_operation_type=direction,
                lines=[{"product_id": product.id}],
            )
            document.fiscal_operation_type = direction
            document.fiscal_line_ids.action_resolve_line()
            self.assertEqual(
                self.env["product.supplierinfo"].search_count(
                    [("partner_id", "=", customer.id)]
                ),
                learned,
            )

    def test_a_product_mapped_for_another_supplier_is_not_resolved(self):
        product = self.env["product.product"].create({"name": "Mapped elsewhere"})
        other = self.env["res.partner"].create({"name": "Another supplier"})
        self.env["product.supplierinfo"].create(
            {
                "partner_id": other.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_code": "SUP-1",
                "price": 1.0,
            }
        )
        with patch.object(
            type(self.env["l10n_br_fiscal.document.line"]),
            "_get_partner_product_code",
            lambda line: "SUP-1",
        ):
            document = self._create_imported_document()
            document._edi_import_suggest()
        self.assertFalse(document.fiscal_line_ids.product_id)
        self.assertEqual(document.fiscal_line_ids.import_state, "pending")

    def test_unknown_unit_stays_pending_by_every_path(self):
        """A unit the supplier declared that matched nothing: the line is pending,
        the confirmation of the suggestions leaves it out, and the document cannot
        be confirmed."""
        product = self.env["product.product"].create({"name": "Matched product"})
        document = self._create_imported_document(
            lines=[
                {"product_id": product.id, "partner_uom_code": "ZZZ"},
                {"product_id": product.id, "partner_uom_code": "UN"},
            ]
        )
        document._edi_import_suggest()
        unknown, known = document.fiscal_line_ids
        self.assertEqual(unknown.import_state, "pending")
        self.assertEqual(known.import_state, "matched")
        # a suggestion whose unit is not confirmed is left out and counted
        unknown.import_state = "matched"
        action = document.action_import_confirm_suggestions()
        self.assertEqual(known.import_state, "resolved")
        self.assertEqual(unknown.import_state, "matched")
        self.assertEqual(action["tag"], "display_notification")
        self.assertIn("1 line(s)", action["params"]["message"])
        self.assertIn("ZZZ", document.import_warning)
        with self.assertRaises(UserError) as error:
            document.action_document_confirm()
        self.assertIn(unknown.name, str(error.exception))

    def test_confirming_the_suggestions_resolves_the_matched_lines_at_once(self):
        product = self.env["product.product"].create({"name": "Matched product"})
        document = self._create_imported_document(
            lines=[{"product_id": product.id}, {"product_id": product.id}]
        )
        self.assertEqual(
            document.fiscal_line_ids.mapped("import_state"), ["matched"] * 2
        )
        self.assertTrue(document.action_import_confirm_suggestions())
        self.assertEqual(document.import_state, "resolved")

    def test_a_document_with_lines_not_reviewed_cannot_be_confirmed(self):
        document = self._create_imported_document()
        with self.assertRaises(UserError) as error:
            document.action_document_confirm()
        self.assertIn("Imported item", str(error.exception))
        self.assertEqual(document.state_edoc, "em_digitacao")

    def test_a_document_with_every_line_reviewed_goes_on_to_the_confirmation(self):
        product = self.env["product.product"].create({"name": "Matched product"})
        document = self._create_imported_document(lines=[{"product_id": product.id}])
        document.action_import_confirm_suggestions()
        with patch.object(
            type(self.Document), "_trigger_fsm", return_value=True
        ) as trigger:
            document.action_document_confirm()
        trigger.assert_called_once()

    def test_a_document_the_company_issued_is_confirmed_as_authorized(self):
        """Issued and authorized in another system, it goes straight to authorized:
        nothing is checked, exported, numbered, sent or turned into an event, and
        the protocol of the file stays."""
        product = self.env["product.product"].create({"name": "Matched product"})
        document = self._create_imported_document(
            issuer="company", lines=[{"product_id": product.id}]
        )
        number = (document.document_number, document.document_serie)
        serie = self.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "9",
                "name": "Series of the file",
                "company_id": self.company.id,
                "document_type_id": document.document_type_id.id,
            }
        )
        event = self.env["l10n_br_fiscal.event"].create(
            {
                "type": "0",
                "company_id": self.company.id,
                "document_id": document.id,
                "document_type_id": document.document_type_id.id,
                "document_serie_id": serie.id,
                "document_number": "1",
                "protocol_number": "135200000000001",
                "origin": "Imported",
                "status_code": "100",
            }
        )
        document.authorization_event_id = event
        document.action_import_confirm_suggestions()
        model = type(self.Document)

        def forbidden(name):
            def fail(*args, **kwargs):
                raise AssertionError(f"{name} must not run")

            return fail

        patchers = [
            patch.object(model, name, forbidden(name))
            for name in (
                "_before_document_validate",
                "_after_document_authorize",
                "_document_check",
                "_document_export",
                "_document_number",
                "_document_send_logic",
                "action_document_send",
            )
        ]
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        document.action_document_confirm()
        self.assertEqual(document.state_edoc, "autorizada")
        self.assertEqual((document.document_number, document.document_serie), number)
        self.assertEqual(document.authorization_protocol, "135200000000001")
        self.assertEqual(document.authorization_event_id, event)
        self.assertEqual(len(document.event_ids), 1)

    def _issuer_vats(self):
        """The company is the issuer of the file."""
        return (("issuer", self.company.partner_id.cnpj_cpf_stripped),)

    def test_a_document_the_company_issued_without_protocol_is_not_authorized(self):
        """The file of a note the company issued has no protocol of authorization:
        the document stays in typing, with a warning, and the confirmation refuses."""
        parsed = self._parsed(KEY_1, status="unknown", company_vats=self._issuer_vats())
        documents, errors, _warnings = self._import(
            [(parsed.file_name, b"x")], [parsed], issuer="company"
        )
        self.assertFalse(errors)
        self.assertTrue(documents.import_without_protocol)
        self.assertIn("no authorization protocol", documents.import_warning)
        with self.assertRaises(UserError):
            documents.action_document_confirm()
        self.assertEqual(documents.state_edoc, "em_digitacao")

    def test_a_note_the_company_issued_with_protocol_does_not_wait_for_it(self):
        parsed = self._parsed(
            KEY_1, status="authorized", company_vats=self._issuer_vats()
        )
        documents, _errors, _warnings = self._import(
            [(parsed.file_name, b"x")], [parsed], issuer="company"
        )
        self.assertFalse(documents.import_without_protocol)
        self.assertNotIn("no authorization protocol", documents.import_warning or "")

    def test_a_note_received_without_protocol_is_only_a_draft_to_review(self):
        parsed = self._parsed(KEY_1, status="unknown")
        documents, _errors, _warnings = self._import(
            [(parsed.file_name, b"x")], [parsed]
        )
        self.assertFalse(documents.import_without_protocol)

    def test_a_document_without_protocol_and_with_lines_to_review_shows_both_causes(
        self,
    ):
        """Both reasons come in the same refusal, not one after the other."""
        parsed = self._parsed(KEY_1, status="unknown", company_vats=self._issuer_vats())
        documents, _errors, _warnings = self._import(
            [(parsed.file_name, b"x")], [parsed], issuer="company"
        )
        self.assertTrue(documents.import_without_protocol)
        self.assertTrue(
            documents.fiscal_line_ids.filtered(
                lambda line: line.import_state in ("pending", "matched")
            )
        )
        with self.assertRaises(UserError) as error:
            documents.action_document_confirm()
        message = error.exception.args[0]
        self.assertIn("lines that were not reviewed", message)
        self.assertIn("no authorization protocol", message)

    def test_a_document_the_company_issued_is_also_refused_with_lines_to_review(self):
        document = self._create_imported_document(issuer="company")
        with self.assertRaises(UserError):
            document.action_document_confirm()

    def test_the_warning_is_unset_when_there_is_nothing_to_say(self):
        document = self._create_imported_document()
        self.assertFalse(document.import_warning)
        document.fiscal_operation_id = False
        self.assertIn("No fiscal operation", document.import_warning)

    def test_the_defaults_of_the_window_do_not_reach_the_documents(self):
        """A window action that calls the import carries ``default_*`` keys for its
        own records (a type of document, a partner): they must not fill the fields
        of the documents and lines the import creates."""
        model = self.Document.with_context(
            default_fiscal_type="nfe",
            default_partner_id=self.supplier.id,
            lang="pt_BR",
        )
        _documents, errors, _warnings = self._import(
            [(f"{KEY_1}.xml", b"<x/>")], parsed=[self._parsed(KEY_1)], model=model
        )
        self.assertFalse(errors)
        self.assertEqual(
            [key for key in self.create_context if key.startswith("default_")], []
        )
        self.assertEqual(self.create_context.get("lang"), "pt_BR")

    def test_a_document_without_lines_has_no_operation_to_suggest(self):
        """An MDF-e of the company has no line, so no CFOP to match an operation: the
        warning that no operation matches the CFOP only makes sense with lines."""
        document = self._create_imported_document(lines=[], fiscal_operation_id=False)
        self.assertFalse(document.fiscal_line_ids)
        self.assertFalse(document.import_warning)

    def test_the_review_is_also_a_state_of_the_list(self):
        document = self._create_imported_document()
        self.assertEqual(document.import_state, "pending")
        self.assertEqual(
            self.Document.search(
                [("imported_document", "=", True), ("import_state", "=", "pending")]
            ),
            document,
        )

    def test_a_note_already_imported_is_found_by_key_and_company(self):
        document = self._create_imported_document(document_key=KEY_3)
        found = self.Document._edi_import_find_existing(
            self._parsed(KEY_3), self.company
        )
        self.assertEqual(found, document)
        self.assertFalse(
            self.Document._edi_import_find_existing(
                self._parsed(KEY_3), self.other_company
            )
        )

    def test_a_user_who_cannot_create_contacts_gets_a_clear_message_per_file(self):
        """The file needs a partner to be registered and the user may not create
        contacts: that file is refused saying so, nothing is created for it, and
        the others of the batch enter."""
        user = self._fiscal_user("fiscal_user_no_partner")
        self.assertFalse(
            self.env["res.partner"]
            .with_user(user)
            .check_access_rights("create", raise_exception=False)
        )
        needs, plain = self._parsed(KEY_1), self._parsed(KEY_2)
        test = self
        document_model = type(self.Document)
        by_name = {needs.file_name: needs, plain.file_name: plain}

        def read(model, name, content):
            return by_name.get(name)

        def create(model, parsed_file, company, role):
            if parsed_file is needs:
                model.env["res.partner"].create({"name": "Needed issuer"})
            return test._create_imported_document(
                company=company, model=model, document_key=parsed_file.access_key
            )

        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.company.ids
        )
        with patch.object(document_model, "_edi_import_read", read), patch.object(
            document_model, "_edi_import_create", create
        ):
            documents, errors, _warnings = model._edi_import_files(
                [(needs.file_name, b"x"), (plain.file_name, b"x")]
            )
        self.assertEqual(documents.mapped("document_key"), [KEY_2])
        self.assertEqual([name for name, _msg in errors], [needs.file_name])
        message = errors[0][1]
        self.assertIn("59.594.315/0001-57", message)
        self.assertIn("not allowed to create contacts", message)
        self.assertIn("import the file again", message)
        self.assertFalse(
            self.env["res.partner"].search([("name", "=", "Needed issuer")])
        )

    def test_any_other_refusal_of_access_is_explained_for_the_file(self):
        """A refusal that is not about contacts is explained too, with what the
        system said, instead of the raw error, and the batch goes on."""
        denied, plain = self._parsed(KEY_1), self._parsed(KEY_2)
        document_model = type(self.Document)
        by_name = {denied.file_name: denied, plain.file_name: plain}
        test = self

        def create(model, parsed_file, company, role):
            if parsed_file is denied:
                raise AccessError(
                    _("You may not create 'Product' (product.product) records.")
                )
            return test._create_imported_document(
                company=company, model=model, document_key=parsed_file.access_key
            )

        with patch.object(
            document_model, "_edi_import_read", lambda m, n, c: by_name.get(n)
        ), patch.object(document_model, "_edi_import_create", create):
            documents, errors, _warnings = self.Document._edi_import_files(
                [(denied.file_name, b"x"), (plain.file_name, b"x")]
            )
        self.assertEqual(documents.mapped("document_key"), [KEY_2])
        message = errors[0][1]
        self.assertIn("product.product", message)
        self.assertIn("you do not have a permission", message)
        self.assertIn(denied.file_name, message)
        self.assertNotIn("contacts", message)

    def test_a_common_fiscal_user_imports_and_learns_as_the_author(self):
        """The fiscal user is not a manager and has no right on purchases: the
        document, the file and the de-para are still born in their name."""
        user = self._fiscal_user("fiscal_user_import")
        product = self.env["product.product"].create({"name": "Learned product"})
        parsed = self._parsed(KEY_1)
        documents, errors, _warnings = self._import(
            [(parsed.file_name, b"x")],
            [parsed],
            model=self.Document.with_user(user).with_context(
                allowed_company_ids=self.company.ids
            ),
            lines=[{"product_id": product.id, "partner_uom_code": "UN"}],
        )
        self.assertEqual((len(documents), errors), (1, []))
        self.assertEqual(documents.create_uid, user)
        self.assertEqual(documents.original_xml_file_id.create_uid, user)
        line = documents.fiscal_line_ids.with_user(user)
        line.action_resolve_line()
        self.assertEqual(line.import_state, "resolved")
        self.assertEqual(line.import_supplierinfo_id.sudo().create_uid, user)
