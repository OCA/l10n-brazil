# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.exceptions import UserError

from .common import KEY_1, KEY_2, EdiImportCase


class TestDocumentImportWizard(EdiImportCase):
    """The window: two things to do, upload the files and read what happened."""

    def _wizard(self, names, user=None):
        """The window with the files uploaded, by ``user`` when given."""
        env = self.env
        if user:
            env = env(
                user=user.id,
                context=dict(env.context, allowed_company_ids=self.company.ids),
            )
        attachments = env["ir.attachment"].create(
            [
                {
                    "name": name,
                    "raw": f"<xml>{name}</xml>".encode(),
                    "res_model": "l10n_br_fiscal_edi.document.import.wizard",
                    "res_id": 0,
                }
                for name in names
            ]
        )
        return env["l10n_br_fiscal_edi.document.import.wizard"].create(
            {"attachment_ids": [(6, 0, attachments.ids)]}
        )

    def _run(self, wizard, parsed=()):
        by_name = {parsed_file.file_name: parsed_file for parsed_file in parsed}
        test = self
        document_model = type(self.Document)

        def read(model, name, content):
            # the reader gets the bytes that were uploaded, nothing else
            if content != f"<xml>{name}</xml>".encode():
                return None
            return by_name.get(name)

        def create(model, parsed_file, company, role):
            return test._create_imported_document(
                company=company, model=model, document_key=parsed_file.access_key
            )

        with patch.object(document_model, "_edi_import_read", read), patch.object(
            document_model, "_edi_import_create", create
        ):
            return wizard.action_import()

    def test_the_window_has_only_the_files(self):
        fields = self.env["l10n_br_fiscal_edi.document.import.wizard"]._fields
        self.assertIn("attachment_ids", fields)
        self.assertNotIn("access_key", fields)

    def test_one_document_opens_its_form(self):
        parsed = self._parsed(KEY_1)
        action = self._run(self._wizard([parsed.file_name]), [parsed])
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "l10n_br_fiscal.document")
        self.assertEqual(action["view_mode"], "form")
        document = self.Document.browse(action["res_id"])
        self.assertEqual(document.document_key, KEY_1)
        self.assertIn(self.company.id, action["context"]["allowed_company_ids"])

    def test_several_documents_open_the_list(self):
        first, second = self._parsed(KEY_1), self._parsed(KEY_2)
        action = self._run(
            self._wizard([first.file_name, second.file_name]), [first, second]
        )
        self.assertEqual(action["view_mode"], "tree,form")
        self.assertEqual(len(self.Document.search(action["domain"])), 2)
        view = self.env.ref("l10n_br_fiscal_edi.document_import_tree")
        self.assertEqual(action["views"][0], (view.id, "tree"))

    def test_the_files_the_window_held_are_removed(self):
        parsed = self._parsed(KEY_1)
        wizard = self._wizard([parsed.file_name])
        attachments = wizard.attachment_ids
        self._run(wizard, [parsed])
        self.assertFalse(attachments.exists())

    def test_a_batch_with_an_error_opens_the_documents_and_tells_what_failed(self):
        parsed = self._parsed(KEY_1)
        action = self._run(self._wizard([parsed.file_name, "garbage.xml"]), [parsed])
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["type"], "warning")
        self.assertIn("garbage.xml", action["params"]["message"])
        self.assertTrue(action["params"]["sticky"])
        self.assertEqual(action["params"]["next"]["type"], "ir.actions.act_window")

    def test_a_note_already_imported_opens_the_document_with_a_notice(self):
        parsed = self._parsed(KEY_1)
        self._run(self._wizard([parsed.file_name]), [parsed])
        action = self._run(self._wizard([parsed.file_name]), [parsed])
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["type"], "info")
        self.assertIn("already imported", action["params"]["message"])
        self.assertEqual(self.Document.search_count([("document_key", "=", KEY_1)]), 1)

    def test_nothing_imported_is_an_error_with_the_reasons(self):
        with self.assertRaises(UserError) as error:
            self._run(self._wizard(["garbage.xml"]))
        self.assertIn("garbage.xml", str(error.exception))
        with self.assertRaises(UserError):
            self._wizard([]).action_import()

    def test_the_files_of_the_inbox_are_imported_without_the_window(self):
        """The DF-e inbox calls the same import, with the document it came from, and
        gets the same answer as the window."""
        parsed = self._parsed(KEY_1)
        dfe_document = object()
        calls = []
        original = type(self.Document)._edi_import_files

        def spy(model, files, dfe_document=None):
            calls.append(dfe_document)
            return original(model, files, dfe_document=dfe_document)

        wizard_model = self.env["l10n_br_fiscal_edi.document.import.wizard"]
        by_name = {parsed.file_name: parsed}
        with patch.object(type(self.Document), "_edi_import_files", spy), patch.object(
            type(self.Document), "_edi_import_read", lambda m, n, c: by_name.get(n)
        ), patch.object(
            type(self.Document),
            "_edi_import_create",
            lambda m, p, c, r: self._create_imported_document(
                company=c, model=m, document_key=p.access_key
            ),
        ):
            action = wizard_model._import_files(
                [(parsed.file_name, b"x")], dfe_document=dfe_document
            )
        self.assertEqual(calls, [dfe_document])
        self.assertEqual(action["res_model"], "l10n_br_fiscal.document")
        self.assertEqual(self.Document.browse(action["res_id"]).document_key, KEY_1)

    def test_the_size_of_the_file_is_never_read_as_its_content(self):
        """The web client asks for the sizes of the binary fields (bin_size): the
        files are read here, from the bytes, and the import works all the same."""
        parsed = self._parsed(KEY_1)
        wizard = self._wizard([parsed.file_name]).with_context(bin_size=True)
        action = self._run(wizard, [parsed])
        self.assertEqual(action["res_model"], "l10n_br_fiscal.document")
        self.assertEqual(self.Document.browse(action["res_id"]).document_key, KEY_1)

    def _menus_of_the_web_client(self, user):
        """Ids of the menus the web client shows to ``user``: the tree it loads, where
        a menu under one that the user does not see never shows."""
        tree = self.env["ir.ui.menu"].with_user(user).load_menus(False)
        return {menu["id"] for menu in tree.values() if isinstance(menu, dict)}

    def test_a_common_fiscal_user_sees_the_menu_and_imports(self):
        user = self._fiscal_user("common_fiscal_user")
        for xmlid in ("document_import_wizard_menu", "imported_document_menu"):
            self.assertIn(
                self.env.ref(f"l10n_br_fiscal_edi.{xmlid}").id,
                self._menus_of_the_web_client(user),
            )
        parsed = self._parsed(KEY_1)
        action = self._run(self._wizard([parsed.file_name], user=user), [parsed])
        document = self.Document.browse(action["res_id"])
        self.assertEqual(document.create_uid, user)
