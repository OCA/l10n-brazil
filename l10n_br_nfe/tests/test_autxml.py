# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import TransactionCase


class TestAutXml(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "AutXML Partner"})
        cls.document = cls.env.ref("l10n_br_nfe.demo_nfe_same_state")

    def _authorize(self, document, partner):
        document.nfe40_autXML = [Command.create({"partner_id": partner.id})]
        return document.nfe40_autXML

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
        the person. Authorizing the accountant on one invoice must not revoke
        the authorization on the others.
        """
        first = self.document.copy()
        second = self.document.copy()

        self._authorize(first, self.partner)
        self._authorize(second, self.partner)

        self.assertEqual(first.nfe40_autXML.partner_id, self.partner)
        self.assertEqual(second.nfe40_autXML.partner_id, self.partner)

    def test_autxml_cnpj_cpf_comes_from_partner(self):
        """The tag CNPJ/CPF is read from the authorized partner."""
        document = self.document.copy()
        authorization = self._authorize(document, self.partner)

        self.assertEqual(authorization.nfe40_CNPJ, self.partner.nfe40_CNPJ)
        self.assertEqual(authorization.nfe40_CPF, self.partner.nfe40_CPF)
