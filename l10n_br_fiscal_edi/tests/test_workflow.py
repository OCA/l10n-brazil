# Copyright (C) 2020  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import UserError
from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_STATE_CANCEL,
    DOCUMENT_STATE_DRAFT,
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
        self.fiscal_document.document_electronic = False
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_DRAFT)

        self.fiscal_document.action_document_confirm()
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_OPEN)

        # For non-electronic, send should move to authorized (simulated completion)
        # Assuming the logic in _document_send_logic handles this
        self.fiscal_document.action_document_send()
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
