# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from unittest.mock import patch

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_STATE_CANCEL
from odoo.addons.l10n_br_fiscal_edi.constants.fiscal import DOCUMENT_STATE_SENDING

DOCUMENT_MODEL = "odoo.addons.l10n_br_fiscal_edi.models.document"
FROM_THE_DOCUMENT = f"{DOCUMENT_MODEL}.Document"


class TestCheckStatus(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.with_key = cls._create_document(
            "35260947786619000137550020000000061765922232"
        )
        cls.without_key = cls._create_document(False)

    @classmethod
    def _create_document(cls, key, state=DOCUMENT_STATE_SENDING):
        return cls.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "document_serie_id": cls.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                "fiscal_operation_type": "out",
                "document_key": key,
                "state_edoc": state,
            }
        )

    def test_a_document_the_issuer_cancelled_is_reported_as_changed(self):
        def cancel_it(document):
            document.state_edoc = DOCUMENT_STATE_CANCEL

        with patch(
            f"{FROM_THE_DOCUMENT}._document_status",
            autospec=True,
            side_effect=cancel_it,
        ):
            action = self.with_key.action_check_status()
        self.assertEqual(self.with_key.state_edoc, DOCUMENT_STATE_CANCEL)
        self.assertIn("Cancelled", action["params"]["message"])
        self.assertTrue(action["params"]["sticky"])

    def test_a_document_that_did_not_move_is_only_counted(self):
        with patch(f"{FROM_THE_DOCUMENT}._document_status", autospec=True):
            action = self.with_key.action_check_status()
        self.assertIn("1", action["params"]["message"])
        self.assertFalse(action["params"]["sticky"])

    def test_a_document_without_a_key_is_named_and_not_asked_about(self):
        with patch(f"{FROM_THE_DOCUMENT}._document_status", autospec=True) as consulted:
            action = self.without_key.action_check_status()
        consulted.assert_not_called()
        self.assertIn(self.without_key.display_name, action["params"]["message"])

    def test_a_document_not_yet_sent_is_skipped(self):
        draft = self._create_document(False, state="em_digitacao")
        with patch(f"{FROM_THE_DOCUMENT}._document_status", autospec=True) as consulted:
            action = draft.action_check_status()
        consulted.assert_not_called()
        self.assertIn("1", action["params"]["message"])

    def test_a_failing_document_does_not_break_the_batch(self):
        def fail_on_with_key(document):
            if document == self.with_key:
                raise ValueError("boom")

        with patch(
            f"{FROM_THE_DOCUMENT}._document_status",
            autospec=True,
            side_effect=fail_on_with_key,
        ):
            action = (self.with_key | self.without_key).action_check_status()
        self.assertIn(self.with_key.display_name, action["params"]["message"])
        self.assertEqual(action["params"]["type"], "danger")

    def test_only_the_limit_is_asked_about_the_rest_is_named(self):
        second = self._create_document("35260947786619000137550020000000061765922233")
        with (
            patch(f"{DOCUMENT_MODEL}.BATCH_STATUS_CHECK_LIMIT", 1),
            patch(f"{FROM_THE_DOCUMENT}._document_status", autospec=True) as consulted,
        ):
            action = (self.with_key | second).action_check_status()
        consulted.assert_called_once()
        self.assertIn("Not asked about this time: 1", action["params"]["message"])

    def test_the_answer_is_a_notification(self):
        with patch(f"{FROM_THE_DOCUMENT}._document_status", autospec=True):
            action = (self.with_key | self.without_key).action_check_status()
        self.assertEqual(action["type"], "ir.actions.client")
        self.assertEqual(action["tag"], "display_notification")
