# Copyright (C) 2020  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import timedelta
from unittest.mock import patch

from erpbrasil.base.fiscal.edoc import ChaveEdoc

from odoo import fields
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


def _key_for_month(year_month):
    """Valid NF-e key (the check digit is computed) for the given YYMM."""
    return ChaveEdoc(
        ano_mes=year_month,
        cnpj_cpf_emitente="00000000000191",
        codigo_uf="35",
        forma_emissao=1,
        modelo_documento="55",
        numero_documento="1",
        numero_serie="1",
        validar=False,
    ).chave


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

    def _confirm_electronic(self):
        self.fiscal_document.document_electronic = True
        self.fiscal_document.action_document_confirm()
        self.assertEqual(self.fiscal_document.state_edoc, DOCUMENT_STATE_OPEN)

    def test_send_with_future_emission_date_uses_now(self):
        """A future emission date makes SEFAZ reject the NF-e (cStat 703)."""
        self._confirm_electronic()
        doc = self.fiscal_document
        before = fields.Datetime.now()
        future = before + timedelta(days=3)
        doc.document_date = future
        doc.date_in_out = future
        doc.action_document_send()
        self.assertGreaterEqual(doc.document_date, before)
        self.assertLessEqual(doc.document_date, fields.Datetime.now())
        # An output date that is not earlier than the emission date is kept
        self.assertEqual(doc.date_in_out, future)

    def test_send_with_future_emission_date_moves_past_date_in_out(self):
        """The output date cannot be earlier than the emission date."""
        self._confirm_electronic()
        doc = self.fiscal_document
        before = fields.Datetime.now()
        doc.document_date = before + timedelta(days=3)
        doc.date_in_out = before - timedelta(days=1)
        doc.action_document_send()
        self.assertGreaterEqual(doc.document_date, before)
        self.assertGreaterEqual(doc.date_in_out, before)
        self.assertGreaterEqual(doc.date_in_out, doc.document_date)

    def test_future_emission_date_is_kept_when_not_issued_by_the_company(self):
        self._confirm_electronic()
        doc = self.fiscal_document
        future = fields.Datetime.now() + timedelta(days=3)
        doc.document_date = future
        doc.issuer = "partner"
        doc._refresh_future_document_date()
        self.assertEqual(doc.document_date, future)

    def test_future_emission_date_is_kept_when_not_electronic(self):
        doc = self.fiscal_document
        future = fields.Datetime.now() + timedelta(days=3)
        doc.document_date = future
        doc.document_electronic = False
        doc._refresh_future_document_date()
        self.assertEqual(doc.document_date, future)

    def test_send_with_future_emission_date_rebuilds_key(self):
        """The document key carries the emission year and month, so it is
        generated again when the new emission date is in another month."""
        self._confirm_electronic()
        doc = self.fiscal_document
        doc.document_date = fields.Datetime.now() + timedelta(days=60)
        # Key of a month other than the current one, as built for the future date
        stale_key = _key_for_month("9901")
        doc.document_key = stale_key

        def fake_generate_key(records):
            for rec in records:
                date = fields.Datetime.context_timestamp(rec, rec.document_date)
                rec.document_key = _key_for_month(date.strftime("%y%m"))

        with patch.object(
            type(doc), "_generate_key", autospec=True, side_effect=fake_generate_key
        ) as generate_key:
            doc.action_document_send()
        generate_key.assert_called_once()
        self.assertNotEqual(doc.document_key, stale_key)
        self.assertEqual(
            doc.document_key[2:6],
            fields.Datetime.context_timestamp(doc, doc.document_date).strftime("%y%m"),
        )

    def test_send_with_future_emission_date_same_month_keeps_key(self):
        self._confirm_electronic()
        doc = self.fiscal_document
        now_local = fields.Datetime.context_timestamp(doc, fields.Datetime.now())
        doc.document_date = fields.Datetime.now() + timedelta(minutes=30)
        key = _key_for_month(now_local.strftime("%y%m"))
        doc.document_key = key
        with patch.object(type(doc), "_generate_key", autospec=True) as generate_key:
            doc.action_document_send()
        generate_key.assert_not_called()
        self.assertEqual(doc.document_key, key)

    def test_send_with_past_emission_date_keeps_it(self):
        self._confirm_electronic()
        doc = self.fiscal_document
        past = fields.Datetime.now() - timedelta(hours=5)
        doc.document_date = past
        doc.action_document_send()
        self.assertEqual(doc.document_date, past)
