# Copyright (C) 2026  KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64

from odoo import _
from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_STATE_CANCEL,
    DOCUMENT_STATE_DRAFT,
)
from odoo.addons.l10n_br_fiscal_edi.constants.fiscal import (
    DOCUMENT_STATE_AUTHORIZED,
    DOCUMENT_STATE_DENIED,
    DOCUMENT_STATE_REJECTED,
)


class TestFiscalNotification(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.env["l10n_br_fiscal.document.email"].with_context(active_test=False).search(
            []
        ).unlink()
        cls.document_type = cls.env.ref("l10n_br_fiscal.document_55")
        cls.template = cls.env.ref(
            "l10n_br_fiscal_notification.fiscal_document_change_state_template"
        )
        cls.template_nfse = cls.env.ref(
            "l10n_br_fiscal_notification.fiscal_document_change_state_template_nfse"
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Partner Test",
                "email": "partner@test.com",
            }
        )
        cls.flagged_contact = cls.env["res.partner"].create(
            {
                "name": "Flagged Contact",
                "parent_id": cls.partner.id,
                "email": "flagged@test.com",
                "edoc_send_email": True,
            }
        )
        cls.plain_contact = cls.env["res.partner"].create(
            {
                "name": "Plain Contact",
                "parent_id": cls.partner.id,
                "email": "plain@test.com",
            }
        )
        cls.definition = cls.env["l10n_br_fiscal.document.email"].create(
            {
                "issuer": "company",
                "state_autorizada": True,
                "state_cancelada": True,
                "email_template_id": cls.template.id,
            }
        )
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": cls.document_type.id,
                "fiscal_operation_type": "out",
                "partner_id": cls.partner.id,
            }
        )

    def test_name_lists_the_notified_states(self):
        """The definition name carries the document type and its states."""
        self.assertEqual(
            self.definition.name,
            _("Others Document Types") + " - Autorizada, Cancelada",
        )
        self.definition.document_type_id = self.document_type
        self.assertEqual(
            self.definition.name,
            f"{self.document_type.name} - Autorizada, Cancelada",
        )

    def test_name_without_any_state(self):
        """A definition with no state ticked is still named."""
        definition = self.env["l10n_br_fiscal.document.email"].create(
            {
                "issuer": "company",
                "document_type_id": self.document_type.id,
                "email_template_id": self.template.id,
            }
        )
        self.assertEqual(definition.name, self.document_type.name)

    def test_no_template_before_authorization(self):
        """Draft and rejected documents select no template."""
        self.assertEqual(self.document.state_edoc, DOCUMENT_STATE_DRAFT)
        self.assertFalse(self.document._get_email_template())

        self.document.state_edoc = DOCUMENT_STATE_REJECTED
        self.assertFalse(self.document._get_email_template())

    def test_no_template_for_unticked_state(self):
        """Denegada is not ticked on the definition, so nothing is selected."""
        self.document.state_edoc = DOCUMENT_STATE_DENIED
        self.assertFalse(self.document._get_email_template())

    def test_template_on_authorization_and_cancellation(self):
        """Both ticked states select the definition template."""
        self.document.state_edoc = DOCUMENT_STATE_AUTHORIZED
        self.assertEqual(self.document._get_email_template(), self.template)

        self.document.state_edoc = DOCUMENT_STATE_CANCEL
        self.assertEqual(self.document._get_email_template(), self.template)

    def test_document_type_definition_wins_over_generic(self):
        """A definition bound to the document type beats the generic one."""
        self.env["l10n_br_fiscal.document.email"].create(
            {
                "issuer": "company",
                "document_type_id": self.document_type.id,
                "state_autorizada": True,
                "email_template_id": self.template_nfse.id,
            }
        )
        self.document.state_edoc = DOCUMENT_STATE_AUTHORIZED
        self.assertEqual(self.document._get_email_template(), self.template_nfse)

    def test_recipients_are_the_flagged_contacts(self):
        """Only contacts with edoc_send_email are picked as recipients."""
        self.assertEqual(self.document._get_email_partners(), self.flagged_contact)

        self.partner.edoc_send_email = True
        self.assertEqual(
            self.document._get_email_partners(),
            self.partner | self.flagged_contact,
        )

    def _mails_sent_by(self, state):
        before = self.env["mail.mail"].sudo().search([])
        self.document.state_edoc = state
        return self.env["mail.mail"].sudo().search([]) - before

    def test_authorization_mails_the_flagged_contacts(self):
        """Authorizing queues a single mail to the flagged contact."""
        self.assertNotIn(self.flagged_contact, self.document.message_partner_ids)

        mails = self._mails_sent_by(DOCUMENT_STATE_AUTHORIZED)

        self.assertEqual(len(mails), 1)
        self.assertIn(self.flagged_contact, mails.recipient_ids)
        self.assertNotIn(self.plain_contact, mails.recipient_ids)
        self.assertIn(self.flagged_contact, self.document.message_partner_ids)

    def test_authorization_attaches_the_document_files(self):
        """The report of the authorized document travels with the mail."""
        report = self.env["ir.attachment"].create(
            {
                "name": "danfe.pdf",
                "datas": base64.b64encode(b"danfe"),
                "mimetype": "application/pdf",
            }
        )
        self.document.file_report_id = report

        mails = self._mails_sent_by(DOCUMENT_STATE_AUTHORIZED)

        self.assertEqual(len(mails), 1)
        self.assertIn(report, mails.attachment_ids)

    def test_rejection_mails_nobody(self):
        """A state with no definition queues no mail at all."""
        mails = self._mails_sent_by(DOCUMENT_STATE_REJECTED)

        self.assertFalse(mails)
        self.assertNotIn(self.flagged_contact, self.document.message_partner_ids)
