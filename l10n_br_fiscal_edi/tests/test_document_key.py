# Copyright 2026 Akretion (Raphaël Valyi <rvalyi@akretion.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_STATE_CANCEL

# Keys already used by the other EDI tests.
DOCUMENT_KEY = "35260912345678000195550020000000061765922237"
OTHER_DOCUMENT_KEY = "35200159594315000157550010000000012062777161"

# ChaveEdoc raises a bare ValueError on a malformed key (erpbrasil), and
# Odoo's test _assertRaises only accepts a single exception class.


class TestDocumentKey(TransactionCase):
    """Access key validation, owned by the EDI module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.document_serie = cls.env.ref("l10n_br_fiscal.document_55_serie_1")

    def _create_document(self, key, document_type="l10n_br_fiscal.document_55"):
        return self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.env.ref(document_type).id,
                "document_serie_id": self.document_serie.id,
                "fiscal_operation_type": "out",
                "document_key": key,
            }
        )

    def test_a_valid_key_is_accepted(self):
        document = self._create_document(DOCUMENT_KEY)
        self.assertEqual(document.document_key, DOCUMENT_KEY)

    def test_an_invalid_key_is_rejected(self):
        # Same key with a wrong check digit.
        with self.assertRaises(ValueError):
            self._create_document(DOCUMENT_KEY[:-1] + "8")

    def test_an_invalid_key_is_rejected_for_any_document_type(self):
        # The document type filter of the duplicate search does not turn
        # off the key validation itself.
        with self.assertRaises(ValueError):
            self._create_document("123", "l10n_br_fiscal.document_01")

    def test_a_duplicated_key_is_rejected(self):
        self._create_document(DOCUMENT_KEY)
        with self.assertRaises(ValidationError):
            self._create_document(DOCUMENT_KEY)

    def test_a_cancelled_document_releases_its_key(self):
        cancelled = self._create_document(DOCUMENT_KEY)
        cancelled.state_edoc = DOCUMENT_STATE_CANCEL
        document = self._create_document(DOCUMENT_KEY)
        self.assertEqual(document.document_key, DOCUMENT_KEY)

    def test_a_related_document_key_is_checked(self):
        values = {"document_type_id": self.env.ref("l10n_br_fiscal.document_55").id}
        related = self.env["l10n_br_fiscal.document.related"].create(
            dict(values, document_key=OTHER_DOCUMENT_KEY)
        )
        self.assertEqual(related.document_key, OTHER_DOCUMENT_KEY)
        with self.assertRaises(ValueError):
            self.env["l10n_br_fiscal.document.related"].create(
                dict(values, document_key=OTHER_DOCUMENT_KEY[:-1] + "8")
            )
