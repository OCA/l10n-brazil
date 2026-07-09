# Copyright (C) 2020  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_STATE_CANCEL,
    DOCUMENT_STATE_DRAFT,
    DOCUMENT_STATE_INVALIDATED,
    DOCUMENT_STATE_OPEN,
)
from odoo.addons.l10n_br_fiscal_edi.constants.fiscal import (
    DOCUMENT_STATE_AUTHORIZED,
    DOCUMENT_STATE_DENIED,
    DOCUMENT_STATE_REJECTED,
)


class TestWorkflow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.fiscal_document = cls.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": cls.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                "fiscal_operation_type": "out",
            }
        )

    def test_no_electronic_01_confirm(self):
        """Non-electronic company docs confirm directly to autorizada
        (no SEFAZ transmission needed). FSM refactor keeps this path."""
        self.fiscal_document.document_electronic = False
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_DRAFT)

        self.fiscal_document.action_document_confirm()
        # Non-electronic docs go straight to autorizada via
        # action_confirm_authorized (runs _before_document_validate
        # for numbering/date/comments).
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_AUTHORIZED)

    def test_electronic_01_confirm(self):
        self.fiscal_document.document_electronic = True
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_DRAFT)

        self.fiscal_document.action_document_confirm()
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_OPEN)

        # Reconfirm should be idempotent (no invalid transition error).
        self.fiscal_document.action_document_confirm()
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_OPEN)

        self.fiscal_document.action_document_send()
        # With "No Processor", it simulates immediate authorization
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_AUTHORIZED)

    def test_electronic_01_rejeitada(self):
        self.fiscal_document.document_electronic = True
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_DRAFT)

        self.fiscal_document.action_document_confirm()

        # Simulate rejection
        self.fiscal_document.state_edoc = DOCUMENT_STATE_REJECTED
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_REJECTED)

        # Retry send
        self.fiscal_document.action_document_send()
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_AUTHORIZED)

    def test_no_electronic_01_draft_cancel(self):
        self.fiscal_document.document_electronic = False
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_DRAFT)

        self.fiscal_document.action_document_cancel()
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_CANCEL)

    def test_electronic_01_draft_cancel(self):
        self.fiscal_document.document_electronic = True
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_DRAFT)

        self.fiscal_document.action_document_cancel()
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_CANCEL)

    def test_electronic_01_back2draft(self):
        self.fiscal_document.document_electronic = True
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_DRAFT)

        self.fiscal_document.action_document_confirm()
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_OPEN)

        self.fiscal_document.action_document_back2draft()
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_DRAFT)

    def test_invalid_transition_raises_user_error(self):
        self.fiscal_document.document_electronic = True
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_DRAFT)

        with self.assertRaises(UserError):
            self.fiscal_document.action_document_send()

    def test_cancel_on_denied_is_idempotent(self):
        self.fiscal_document.document_electronic = True
        self.fiscal_document.state_edoc = DOCUMENT_STATE_DENIED

        self.fiscal_document.action_document_cancel()
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_DENIED)

    def test_partner_issuer_confirm_idempotent(self):
        """Test that confirming a partner-issued doc multiple times is idempotent.

        Regression test for the bug fixed in OCA/l10n-brazil#4364 where
        action_document_confirm() would fail on the second call because
        the document was already in a confirmed state.

        With the FSM refactor, partner-issued docs go directly to AUTHORIZED
        (the supplier already authorized the document, no SEFAZ transmission
        needed), and calling confirm again is a safe no-op because the FSM
        detects the document is already confirmed.
        """
        self.fiscal_document.document_electronic = True
        self.fiscal_document.issuer = "partner"

        self.assertEqual(
            self.fiscal_document.state_edoc,
            DOCUMENT_STATE_DRAFT,
        )

        # First confirm - partner-issued docs go directly to AUTHORIZED
        # (the document was already authorized by the supplier, no SEFAZ
        # transmission needed from the company's side)
        self.fiscal_document.action_document_confirm()
        self.assertEqual(
            self.fiscal_document.state_edoc,
            DOCUMENT_STATE_AUTHORIZED,
        )

        # Second confirm - must NOT raise an error (idempotent)
        self.fiscal_document.action_document_confirm()
        self.assertEqual(
            self.fiscal_document.state_edoc,
            DOCUMENT_STATE_AUTHORIZED,
        )

    def test_correction_wizard(self):
        """The correction wizard flow must work end to end.

        Regression test: the wizard calls _document_correction(), which was
        dropped together with the legacy workflow mixin (as well as the
        correction_reason field), breaking the Correction (CC-e) flow with
        an AttributeError.
        """
        self.fiscal_document.document_electronic = True
        self.fiscal_document.action_document_confirm()
        self.fiscal_document.action_document_send()
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_AUTHORIZED)

        action = self.fiscal_document.action_document_correction()
        self.assertEqual(
            action["res_model"], "l10n_br_fiscal.document.correction.wizard"
        )
        wizard = self.env["l10n_br_fiscal.document.correction.wizard"].create(
            {
                "document_id": self.fiscal_document.id,
                "justification": "Correction of additional data",
            }
        )
        wizard.doit()
        self.assertEqual(
            self.fiscal_document.correction_reason, "Correction of additional data"
        )

    def test_transmission_hooks_exist(self):
        """Hooks called with super() by transmission modules (l10n_br_nfe,
        l10n_br_cte, l10n_br_mdfe, l10n_br_nfse_focus) and by the document
        status wizard are part of the stable API and must exist on the base
        EDI document."""
        self.assertIsNone(self.fiscal_document._document_status())
        self.assertIsNone(self.fiscal_document._edoc_processor())
        self.assertIsNone(self.fiscal_document._validate_xml("<xml/>"))
        self.assertFalse(self.fiscal_document._direct_draft_send())

    def test_cancel_on_invalidated_document(self):
        """'inutilizada' is a valid state_edoc value: cancelling such a
        document must be a no-op and any other trigger must raise a
        UserError — not a raw ValueError while building the state machine,
        which knew nothing about this state."""
        self.fiscal_document.document_electronic = True
        self.fiscal_document.state_edoc = DOCUMENT_STATE_INVALIDATED

        self.fiscal_document.action_document_cancel()
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_INVALIDATED)

        with self.assertRaises(UserError):
            self.fiscal_document.action_document_send()

    def test_dashboard_counts_authorized(self):
        """The operation dashboard 'authorized' counter must count
        authorized documents, not merely confirmed (open) ones."""
        operation = self.env.ref("l10n_br_fiscal.fo_venda")
        self.fiscal_document.fiscal_operation_id = operation
        self.fiscal_document.document_electronic = True

        self.fiscal_document.action_document_confirm()
        before = operation.get_operation_dashboard_data()["number_authorized"]

        self.fiscal_document.action_document_send()
        after = operation.get_operation_dashboard_data()["number_authorized"]
        self.assertEqual(after, before + 1)

    def test_operation_comments_copied_on_confirm(self):
        """Comments configured on the fiscal operation must be copied to the
        document upon confirmation.

        Regression test: this was done by the legacy _document_confirm(),
        dropped by the FSM refactor without replacement, so documents were
        confirmed with empty additional data.
        """
        comment = self.env["l10n_br_fiscal.comment"].create(
            {
                "name": "Operation comment",
                "comment": "Goods sold under fiscal benefit",
                "comment_type": "fiscal",
                "object": "l10n_br_fiscal.document.mixin",
            }
        )
        operation = self.env.ref("l10n_br_fiscal.fo_venda")
        operation.comment_ids |= comment
        self.fiscal_document.document_electronic = True
        self.fiscal_document.fiscal_operation_id = operation
        self.fiscal_document.action_document_confirm()
        self.assertIn(comment, self.fiscal_document.comment_ids)

    def test_after_authorize_hook_called(self):
        """The action_authorize transition must fire the
        _after_document_authorize callback (transmission modules rely on it,
        e.g. l10n_br_nfe generates the DANFE there)."""
        self.fiscal_document.document_electronic = True
        self.fiscal_document.action_document_confirm()
        with patch.object(
            type(self.fiscal_document), "_after_document_authorize"
        ) as hook:
            self.fiscal_document.action_document_send()
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_AUTHORIZED)
        hook.assert_called()

    def test_direct_draft_send(self):
        """Documents whose _direct_draft_send() returns True must be sent
        right after confirmation (POS/NFC-e style flow)."""
        self.fiscal_document.document_electronic = True
        with patch.object(
            type(self.fiscal_document), "_direct_draft_send", return_value=True
        ):
            self.fiscal_document.action_document_confirm()
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_AUTHORIZED)

    def test_partner_issuer_not_locked_when_open(self):
        """Supplier bills (issuer=partner) stay editable after confirm.

        Partner-issued docs are local records of a third-party document,
        so their identity fields must remain editable once out of draft;
        only company-issued docs lock. They lock only when cancelled.
        """
        self.fiscal_document.document_electronic = True
        self.fiscal_document.issuer = "partner"
        self.fiscal_document.action_document_confirm()
        # Partner-issued docs go directly to AUTHORIZED (no SEFAZ
        # transmission needed from the company's side) but stay unlocked.
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_AUTHORIZED)

        # not locked -> identity field write is allowed
        self.assertFalse(self.fiscal_document.edoc_is_locked)
        self.fiscal_document.document_date = "2026-01-01 00:00:00"

        # a company-issued doc in the same state IS locked
        company_doc = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                "fiscal_operation_type": "out",
                "issuer": "company",
            }
        )
        company_doc.document_electronic = True
        company_doc.action_document_confirm()
        self.assertTrue(company_doc.edoc_is_locked)
