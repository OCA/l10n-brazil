# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from lxml import etree

from odoo.tests import tagged
from odoo.tools.safe_eval import safe_eval

from .common import EdiImportCase


@tagged("post_install", "-at_install")
class TestImportViews(EdiImportCase):
    """Every view of the import loads, and every field it names exists."""

    def _check_fields(self, model_name, arch):
        """Fields named in ``arch`` exist in ``model_name``; the sub views of the
        x2many fields are checked against the model of the field."""
        model = self.env[model_name]
        root = etree.fromstring(arch) if isinstance(arch, str) else arch
        for node in root.iterchildren():
            self._check_node(model, node)

    def _check_node(self, model, node):
        if node.tag == "field":
            name = node.get("name")
            self.assertIn(name, model._fields, f"{model._name} has no field {name}")
            comodel = model._fields[name].comodel_name
            for sub_view in node.iterchildren("tree", "form", "kanban"):
                for child in sub_view.iterchildren():
                    self._check_node(self.env[comodel], child)
            return
        for child in node.iterchildren():
            self._check_node(model, child)

    def test_the_document_views_load_and_name_existing_fields(self):
        for view_type in ("form", "tree", "search"):
            arch = self.Document.get_view(view_type=view_type)["arch"]
            self._check_fields("l10n_br_fiscal.document", arch)
        for xmlid in ("document_import_tree", "document_import_search"):
            view = self.env.ref(f"l10n_br_fiscal_edi.{xmlid}")
            arch = self.Document.get_view(view.id)["arch"]
            self._check_fields("l10n_br_fiscal.document", arch)

    def test_the_form_has_the_review_the_page_and_the_button(self):
        user = self._fiscal_user("view_fiscal_user")
        arch = (
            self.Document.with_user(user)
            .with_context(allowed_company_ids=user.company_ids.ids)
            .get_view(view_type="form")["arch"]
        )
        form = etree.fromstring(arch)
        self.assertTrue(
            form.xpath("//button[@name='action_import_confirm_suggestions']")
        )
        self.assertTrue(
            form.xpath(
                "//page[@name='edi_payment']//field[@name='edi_payment_summary']"
            )
        )
        self.assertTrue(form.xpath("//field[@name='import_warning']"))
        self.assertTrue(
            form.xpath("//button[@name='action_import_check_partners_again']")
        )
        create = form.xpath("//button[@name='action_import_create_products']")
        self.assertTrue(create)
        # offered only while there is a product to create
        self.assertIn("import_missing_products", create[0].get("modifiers"))

    def test_the_confirm_button_of_an_imported_document_is_given_back(self):
        """Another module (the NF-e) hides the button to confirm for an imported
        document. A common fiscal user must still see it on the form, of a document
        received and of one the company issued, to confirm after the review."""
        self.env["ir.ui.view"].create(
            {
                "name": "hides the confirm button of an imported document",
                "model": "l10n_br_fiscal.document",
                "inherit_id": self.env.ref("l10n_br_fiscal.document_form").id,
                "arch": """<xpath
                    expr="//header/button[@name='action_document_confirm']"
                    position="attributes">
                    <attribute name="attrs">{'invisible': ['|',
                    ('state_edoc', '!=', 'em_digitacao'),
                    ('imported_document', '=', True)]}</attribute>
                </xpath>""",
            }
        )
        user = self._fiscal_user("confirm_fiscal_user")
        arch = (
            self.Document.with_user(user)
            .with_context(allowed_company_ids=user.company_ids.ids)
            .get_view(view_type="form")["arch"]
        )
        button = etree.fromstring(arch).xpath(
            "//button[@name='action_document_confirm']"
        )[0]
        modifiers = json.loads(button.get("modifiers"))
        self.assertEqual(modifiers["invisible"], [["state_edoc", "!=", "em_digitacao"]])

    def test_the_line_form_names_existing_fields(self):
        line_model = self.env["l10n_br_fiscal.document.line"]
        arch = line_model.get_view(view_type="form")["arch"]
        self._check_fields("l10n_br_fiscal.document.line", arch)
        form = etree.fromstring(arch)
        for name in ("import_state", "import_uom_id", "import_uom_factor"):
            self.assertTrue(form.xpath(f"//field[@name='{name}']"), name)
        self.assertTrue(form.xpath("//button[@name='action_resolve_line']"))

    def test_the_unit_of_the_review_is_searched_by_code_and_alias(self):
        form = etree.fromstring(
            self.env["l10n_br_fiscal.document.line"].get_view(view_type="form")["arch"]
        )
        field = form.xpath("//field[@name='import_uom_id']")[0]
        self.assertIn("uom_search_fiscal_code", field.get("context"))

    def test_the_window_view_loads(self):
        wizard = self.env["l10n_br_fiscal_edi.document.import.wizard"]
        self._check_fields(wizard._name, wizard.get_view(view_type="form")["arch"])

    def test_the_list_of_imported_documents_does_not_assume_a_direction(self):
        """Documents received and documents the company issued are both listed,
        and a new one is not created as an entry."""
        action = self.env.ref("l10n_br_fiscal_edi.imported_document_action")
        self.assertNotIn("fiscal_operation_type", action.context or "")
        received = self._create_imported_document()
        own = self._create_imported_document(issuer="company")
        own.fiscal_operation_type = "out"
        listed = self.Document.search(safe_eval(action.domain))
        self.assertIn(received, listed)
        self.assertIn(own, listed)

    def test_the_actions_open_the_right_views(self):
        action = self.env.ref("l10n_br_fiscal_edi.imported_document_action")
        self.assertEqual(
            action.view_id, self.env.ref("l10n_br_fiscal_edi.document_import_tree")
        )
        self.assertEqual(
            action.search_view_id,
            self.env.ref("l10n_br_fiscal_edi.document_import_search"),
        )
        self.assertEqual(
            self.env.ref("l10n_br_fiscal_edi.document_import_wizard_action").target,
            "new",
        )
