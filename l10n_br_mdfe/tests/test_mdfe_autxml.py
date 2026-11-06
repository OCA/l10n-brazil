# Copyright 2026 Engenere.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import TransactionCase

from .tools import load_mdfe_fixture_files


class TestMDFeAutXml(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_mdfe_fixture_files(cls.env)
        cls.document = cls.env.ref("l10n_br_mdfe.demo_mdfe_lc_modal_rodoviario")
        cls.accountant = cls.env["res.partner"].create({"name": "Accountant"})

    def test_autxml_comes_from_the_document_company(self):
        """The accountant authorized is the one of the document company.

        Not the one of the company the user is working on, which may be
        another one in the company switcher.
        """
        company = self.document.company_id
        other_company = self.env["res.company"].search(
            [("id", "!=", company.id)], limit=1
        )
        other_accountant = self.env["res.partner"].create(
            {"name": "Other Company Accountant"}
        )
        company.accountant_id = self.accountant
        other_company.accountant_id = other_accountant

        document = self.document.with_context(
            allowed_company_ids=[other_company.id, company.id]
        ).copy()

        self.assertEqual(document.env.company, other_company)
        self.assertIn(self.accountant, document.mdfe30_autXML.partner_id)
        self.assertNotIn(other_accountant, document.mdfe30_autXML.partner_id)

    def test_document_created_with_autxml_keeps_it(self):
        """A document created with its own autXML (an import) keeps it."""
        self.document.company_id.accountant_id = self.accountant
        given_partner = self.env["res.partner"].create({"name": "Given Partner"})

        document = self.document.copy(
            {"mdfe30_autXML": [Command.create({"partner_id": given_partner.id})]}
        )

        self.assertEqual(document.mdfe30_autXML.partner_id, given_partner)

    def test_new_document_keeps_the_authorization_of_the_previous(self):
        """Creating a document does not take the accountant from another one."""
        self.document.company_id.accountant_id = self.accountant

        first = self.document.copy()
        second = self.document.copy()

        self.assertEqual(len(first.mdfe30_autXML), 1)
        self.assertEqual(len(second.mdfe30_autXML), 1)

    def test_user_without_contact_rights_creates_document(self):
        """The accountant default does not write on the contact."""
        self.document.company_id.accountant_id = self.accountant
        user = self.env["res.users"].create(
            {
                "name": "Fiscal User",
                "login": "mdfe_autxml_fiscal_user",
                "company_id": self.document.company_id.id,
                "company_ids": [Command.set(self.document.company_id.ids)],
                "group_ids": [
                    Command.set(
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("l10n_br_fiscal.group_user").id,
                        ]
                    )
                ],
            }
        )

        document = self.document.with_user(user).copy()

        self.assertEqual(len(document.mdfe30_autXML), 1)
