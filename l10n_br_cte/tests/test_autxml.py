# Copyright 2026 Engenere.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import TransactionCase


class TestAutXml(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "AutXML Partner"})
        cls.document = cls.env.ref("l10n_br_cte.demo_cte_lc_modal_rodoviario")

    def _authorize(self, document, partner):
        document.cte40_autXML = [Command.create({"partner_id": partner.id})]
        return document.cte40_autXML

    def test_unlink_document_keeps_autxml_partner(self):
        """Deleting a fiscal document must not delete the authorized partner."""
        document = self.document.copy()
        self._authorize(document, self.partner)

        document.unlink()

        self.assertTrue(
            self.partner.exists(),
            "deleting a fiscal document must not delete the partner "
            "authorized to download its XML",
        )

    def test_unlink_document_removes_authorization(self):
        """The authorization record itself must go with the document."""
        document = self.document.copy()
        authorization = self._authorize(document, self.partner)

        document.unlink()

        self.assertFalse(
            authorization.exists(),
            "an authorization is meaningless without its document",
        )

    def test_partner_authorized_on_several_documents(self):
        """The same partner may be authorized on several documents.

        The autXML tag is the authorization of a person on that document, not
        the person. Authorizing the accountant on one CT-e must not revoke
        the authorization on the others.
        """
        first = self.document.copy()
        second = self.document.copy()

        self._authorize(first, self.partner)
        self._authorize(second, self.partner)

        self.assertEqual(first.cte40_autXML.partner_id, self.partner)
        self.assertEqual(second.cte40_autXML.partner_id, self.partner)

    def test_autxml_cnpj_cpf_comes_from_partner(self):
        """The tag CNPJ/CPF is read from the authorized partner."""
        document = self.document.copy()
        authorization = self._authorize(document, self.partner)

        self.assertEqual(authorization.cte40_CNPJ, self.partner.cte40_CNPJ)
        self.assertEqual(authorization.cte40_CPF, self.partner.cte40_CPF)

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
        company.accountant_id = self.partner
        other_company.accountant_id = other_accountant

        document = self.document.with_context(
            allowed_company_ids=[other_company.id, company.id]
        ).copy()

        self.assertEqual(document.env.company, other_company)
        self.assertIn(self.partner, document.cte40_autXML.partner_id)
        self.assertNotIn(other_accountant, document.cte40_autXML.partner_id)

    def test_document_created_with_autxml_keeps_it(self):
        """A document created with its own autXML (an import) keeps it."""
        self.document.company_id.accountant_id = self.partner
        given_partner = self.env["res.partner"].create({"name": "Given Partner"})

        document = self.document.copy(
            {"cte40_autXML": [Command.create({"partner_id": given_partner.id})]}
        )

        self.assertEqual(document.cte40_autXML.partner_id, given_partner)
