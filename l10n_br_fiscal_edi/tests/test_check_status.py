# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from unittest.mock import patch

from odoo.tests import TransactionCase

FROM_THE_DOCUMENT = "odoo.addons.l10n_br_fiscal_edi.models.document.Document"


class TestCheckStatus(TransactionCase):
    """Asking the SEFAZ about a selection and saying what moved.

    A note issued by someone else only changes at the SEFAZ: the issuer cancels
    it and nothing on this side knows until somebody asks. The consult itself
    and the state map already existed and are covered elsewhere; what is tested
    here is walking the selection and reporting the outcome, because the point
    of asking about twenty notes is the two that changed.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.with_key = cls._create_document(
            "35260947786619000137550020000000061765922232"
        )
        cls.without_key = cls._create_document(False)

    @classmethod
    def _create_document(cls, key):
        return cls.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "document_serie_id": cls.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                "fiscal_operation_type": "out",
                "document_key": key,
            }
        )

    def test_a_document_the_issuer_cancelled_is_reported_as_changed(self):
        def cancel_it(document):
            document.state_edoc = "cancelada"

        with patch(
            f"{FROM_THE_DOCUMENT}._document_status",
            autospec=True,
            side_effect=cancel_it,
        ):
            action = self.with_key.action_check_status()
        self.assertEqual(self.with_key.state_edoc, "cancelada")
        self.assertIn("cancelada", action["params"]["message"])
        self.assertTrue(action["params"]["sticky"])

    def test_a_document_that_did_not_move_is_only_counted(self):
        with patch(f"{FROM_THE_DOCUMENT}._document_status", autospec=True):
            action = self.with_key.action_check_status()
        message = action["params"]["message"]
        self.assertIn("1", message)
        self.assertFalse(action["params"]["sticky"])

    def test_a_document_without_a_key_is_named_and_not_asked_about(self):
        """There is nothing to ask the SEFAZ about a document that never got a
        key, and silently doing nothing would look like the answer was 'no
        change'."""
        with patch(f"{FROM_THE_DOCUMENT}._document_status", autospec=True) as consulted:
            action = self.without_key.action_check_status()
        consulted.assert_not_called()
        self.assertIn(self.without_key.display_name, action["params"]["message"])

    def test_the_answer_is_a_notification(self):
        with patch(f"{FROM_THE_DOCUMENT}._document_status", autospec=True):
            action = (self.with_key | self.without_key).action_check_status()
        self.assertEqual(action["type"], "ir.actions.client")
        self.assertEqual(action["tag"], "display_notification")
