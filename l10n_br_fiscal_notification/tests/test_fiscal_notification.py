# Copyright 2026 Engenere - Felipe Motter Pereira
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from unittest.mock import patch

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_STATE_CANCEL
from odoo.addons.l10n_br_fiscal_edi.constants.fiscal import (
    DOCUMENT_STATE_AUTHORIZED,
    DOCUMENT_STATE_SENDING,
)


def fake_after_document_authorize(self):
    """Stand-in for l10n_br_nfe, which generates the DANFE in this callback."""
    self.file_report_id = self.env["ir.attachment"].create(
        {
            "name": "danfe.pdf",
            "raw": b"%PDF-1.4 fake DANFE",
            "res_model": self._name,
            "res_id": self.id,
        }
    )


class TestFiscalNotification(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.document_model = cls.env["l10n_br_fiscal.document"]
        template = cls.env["mail.template"].create(
            {
                "name": "Fiscal document notification",
                "model_id": cls.env.ref(
                    "l10n_br_fiscal.model_l10n_br_fiscal_document"
                ).id,
                "subject": "Fiscal document",
                "email_to": "customer@example.com",
            }
        )
        for state in (DOCUMENT_STATE_AUTHORIZED, DOCUMENT_STATE_CANCEL):
            cls.env["l10n_br_fiscal.document.email"].create(
                {"state_edoc": state, "email_template_id": template.id}
            )
        cls.document = cls.document_model.create(
            {
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "document_serie_id": cls.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                "fiscal_operation_type": "out",
            }
        )

    def _mails(self):
        return self.env["mail.mail"].search(
            [("model", "=", self.document._name), ("res_id", "=", self.document.id)]
        )

    def _new_mails(self, before):
        """E-mails of the step under test only: the demo data of this module
        adds definitions valid for any state, so the setup writes mail too."""
        return self._mails() - before

    def _patch_after_authorize(self):
        return patch.object(
            type(self.document_model),
            "_after_document_authorize",
            fake_after_document_authorize,
        )

    def test_authorize_mails_the_danfe_generated_after_the_state_write(self):
        self.document.document_electronic = True
        self.document.write({"state_edoc": DOCUMENT_STATE_SENDING})
        before = self._mails()
        with self._patch_after_authorize():
            self.document._trigger_fsm("action_authorize")
        mails = self._new_mails(before)
        self.assertEqual(self.document.state_edoc, DOCUMENT_STATE_AUTHORIZED)
        self.assertEqual(len(mails), 1, "one e-mail, not one per path")
        self.assertIn(self.document.file_report_id, mails.attachment_ids)

    def test_confirm_straight_to_authorized_mails_after_the_callbacks(self):
        """Non-electronic documents use the action_confirm_authorized transition.

        That path does not generate a real DANFE: the stand-in only proves the
        e-mail waits for the after callbacks in the second transition too.
        """
        self.document.document_electronic = False
        before = self._mails()
        with self._patch_after_authorize():
            self.document.action_document_confirm()
        mails = self._new_mails(before)
        self.assertEqual(self.document.state_edoc, DOCUMENT_STATE_AUTHORIZED)
        self.assertEqual(len(mails), 1)
        self.assertIn(self.document.file_report_id, mails.attachment_ids)

    def test_direct_write_to_authorized_still_mails(self):
        before = self._mails()
        self.document.write({"state_edoc": DOCUMENT_STATE_AUTHORIZED})
        self.assertEqual(len(self._new_mails(before)), 1)

    def test_state_machine_cancel_still_mails_from_write(self):
        before = self._mails()
        self.document._trigger_fsm("action_cancel_fsm")
        self.assertEqual(self.document.state_edoc, DOCUMENT_STATE_CANCEL)
        self.assertEqual(len(self._new_mails(before)), 1)

    def test_authorized_email_is_the_last_after_callback(self):
        transitions = [
            transition
            for transition in self.document.get_state_machine_config()["transitions"]
            if transition.get("dest") == DOCUMENT_STATE_AUTHORIZED
        ]
        self.assertTrue(transitions)
        for transition in transitions:
            self.assertIn("_after_document_authorize", transition["after"])
            self.assertEqual(transition["after"][-1], "_send_authorized_email")
