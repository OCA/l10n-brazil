# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import importlib
import json

from lxml import etree

from odoo.tests import tagged

from .common import EdiImportCase

# the types of document the import brings, and the module that reads each one
TYPES = {"55": "l10n_br_nfe", "57": "l10n_br_cte", "58": "l10n_br_mdfe", "SE": None}


@tagged("post_install", "-at_install")
class TestImportScreens(EdiImportCase):
    """What a common fiscal user sees of an imported document, whatever the modules
    of the series that are installed along with this one."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls._fiscal_user(cls, "screen_fiscal_user", form_groups=True)

    def _installed(self, module):
        return bool(
            self.env["ir.module.module"].search_count(
                [("name", "=", module), ("state", "=", "installed")]
            )
        )

    def _as_user(self, records):
        return records.with_user(self.user).with_context(
            allowed_company_ids=self.user.company_ids.ids
        )

    def _read_screen(self, records, view_type="form"):
        """What the web client does to open a record: the view, then the fields the
        view names, and the sub views of the x2many fields, for the user."""
        records = self._as_user(records)
        arch = etree.fromstring(records.get_view(view_type=view_type)["arch"])
        self._read_fields(records, arch)

    def _read_fields(self, records, arch):
        names = set()
        for node in arch.iterchildren():
            self._collect(node, records, names)
        records.read(sorted(names))

    def _collect(self, node, records, names):
        if node.tag == "field":
            name = node.get("name")
            if name not in records._fields:
                return
            names.add(name)
            for sub_view in node.iterchildren("tree", "form", "kanban"):
                self._read_fields(records[name][:3], sub_view)
            return
        for child in node.iterchildren():
            self._collect(child, records, names)

    def _document_of(self, code, **values):
        document_type = self.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", code)], limit=1
        )
        if not document_type:
            self.skipTest(f"No document type {code}")
        values.setdefault("issuer", "partner")
        return self._create_imported_document(
            document_type_id=document_type.id, **values
        )

    def test_the_user_opens_the_document_and_its_line_of_every_type(self):
        for code in TYPES:
            for issuer in ("partner", "company"):
                with self.subTest(type=code, issuer=issuer):
                    document = self._document_of(code, issuer=issuer)
                    self._read_screen(document, "form")
                    self._read_screen(document, "tree")
                    self._read_screen(document.fiscal_line_ids, "form")

    def test_the_new_menus_are_visible_to_the_user(self):
        visible = self.env["ir.ui.menu"].with_user(self.user)._visible_menu_ids()
        for xmlid in (
            "l10n_br_fiscal_edi.document_import_wizard_menu",
            "l10n_br_fiscal_edi.imported_document_menu",
        ):
            with self.subTest(menu=xmlid):
                self.assertIn(self.env.ref(xmlid).id, visible)

    def test_the_button_to_confirm_is_visible_to_the_user(self):
        for code in TYPES:
            with self.subTest(type=code):
                document = self._as_user(self._document_of(code))
                arch = etree.fromstring(document.get_view(view_type="form")["arch"])
                button = arch.xpath("//button[@name='action_document_confirm']")
                self.assertTrue(button)
                modifiers = json.loads(button[0].get("modifiers") or "{}")
                self.assertEqual(
                    modifiers.get("invisible"), [["state_edoc", "!=", "em_digitacao"]]
                )

    def test_a_cte_with_installments_and_no_operation_shows_its_amounts(self):
        """The amounts of the page come from the lines when the document has no
        operation, so the page is not left at zero and warns of nothing."""
        if not self._installed("l10n_br_cte"):
            self.skipTest("l10n_br_cte is not installed")
        try:
            module = importlib.import_module(
                "odoo.addons.l10n_br_cte.tests.test_cte_document_import"
            )
        except ImportError:
            self.skipTest("l10n_br_cte has no import tests to take the sample from")
        documents, errors, _warnings = self.Document._edi_import_files(
            [("cte.xml", module.cte_xml(module.COLLECTION))]
        )
        self.assertFalse(errors)
        self.assertFalse(documents.fiscal_operation_id)
        values = documents._edi_payment_summary_values()
        self.assertEqual([amount for _label, amount in values["totals"]], [100, 0, 100])
        self.assertEqual(len(values["installments"]), 2)
        self.assertFalse(values["warning"])
        self.assertFalse(documents._edi_installment_warning())
