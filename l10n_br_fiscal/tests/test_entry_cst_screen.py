# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

import json

from lxml import etree

from odoo.tests import TransactionCase, tagged

from .common_view_fields import ViewFieldsCheck

ENTRY_CST_PAGES = {
    "entry_ipi_cst_id": "ipi",
    "entry_pis_cst_id": "pis",
    "entry_cofins_cst_id": "cofins",
}


@tagged("post_install", "-at_install")
class TestEntryCstScreen(ViewFieldsCheck, TransactionCase):
    def _arch(self, model, xmlid, user=None):
        view = self.env.ref(xmlid)
        records = self.env[model].with_user(user) if user else self.env[model]
        return etree.fromstring(records.get_view(view.id)["arch"])

    def test_entry_cst_fields_on_the_tax_pages_read_only(self):
        form = self._arch(
            "l10n_br_fiscal.document.line", "l10n_br_fiscal.document_line_form"
        )
        for name, page in ENTRY_CST_PAGES.items():
            nodes = form.xpath(f"//page[@name='{page}']//field[@name='{name}']")
            self.assertEqual(len(nodes), 1, name)
            previous = nodes[0].getprevious()
            self.assertEqual(previous.get("name"), f"{page}_cst_code", name)
            modifiers = json.loads(nodes[0].get("modifiers"))
            self.assertTrue(modifiers.get("readonly"), name)
            self.assertEqual(
                modifiers.get("invisible"), [[name, "=", False]], "shown when filled"
            )
        benefit = form.xpath("//field[@name='partner_icms_tax_benefit_code']")
        self.assertEqual(len(benefit), 1)
        self.assertTrue(json.loads(benefit[0].get("modifiers")).get("readonly"))

    def test_entry_cst_fields_are_added_only_once(self):
        form = self._arch(
            "l10n_br_fiscal.document.line", "l10n_br_fiscal.document_line_form"
        )
        form = self.env["l10n_br_fiscal.document.line"]._add_entry_cst_fields(form)
        for name in ENTRY_CST_PAGES:
            self.assertEqual(len(form.xpath(f"//field[@name='{name}']")), 1, name)

    def test_shared_fiscal_template_has_no_entry_cst_field(self):
        template = etree.fromstring(
            self.env.ref("l10n_br_fiscal.document_fiscal_line_mixin_form").arch
        )
        for name in ENTRY_CST_PAGES:
            self.assertFalse(template.xpath(f"//field[@name='{name}']"), name)
        self.assertTrue(
            template.xpath("//field[@name='partner_icms_tax_benefit_code']")
        )

    def test_recompute_button_only_for_imported_document_in_typing(self):
        form = self._arch(
            "l10n_br_fiscal.document",
            "l10n_br_fiscal.document_form",
            user=self.env.ref("base.user_admin"),
        )
        buttons = form.xpath("//header/button[@name='action_recompute_entry_cst']")
        self.assertEqual(len(buttons), 1)
        self.assertEqual(
            json.loads(buttons[0].get("modifiers")).get("invisible"),
            [
                "|",
                ["imported_document", "=", False],
                ["state_edoc", "!=", "em_digitacao"],
            ],
        )

    def test_every_field_of_the_fiscal_document_views_exists(self):
        checked = self.check_view_fields(
            ("l10n_br_fiscal.document", "l10n_br_fiscal.document.line")
        )
        self.assertTrue(checked)
