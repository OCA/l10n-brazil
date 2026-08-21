# Copyright (C) 2020  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_REJEITADA,
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
        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_EM_DIGITACAO
        ), "Error with document workflow, state 'SITUACAO_EDOC_A_ENVIAR' "

        self.fiscal_document.action_document_confirm()
        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_A_ENVIAR
        ), "Error with document workflow, state 'SITUACAO_EDOC_A_ENVIAR' "

        self.fiscal_document.action_document_send()
        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_AUTORIZADA
        ), "Error with document workflow, state 'SITUACAO_EDOC_AUTORIZADA' "

    def test_electronic_01_confirm(self):
        self.fiscal_document.document_electronic = True

        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_EM_DIGITACAO
        ), "Error with document workflow, state 'SITUACAO_EDOC_A_ENVIAR' "

        self.fiscal_document.action_document_confirm()
        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_A_ENVIAR
        ), "Error with document workflow, state 'SITUACAO_EDOC_A_ENVIAR' "

        self.fiscal_document.action_document_send()
        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_AUTORIZADA
        ), "Error with document workflow, state 'SITUACAO_EDOC_AUTORIZADA' "

    def test_electronic_01_rejeitada(self):
        self.fiscal_document.document_electronic = True

        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_EM_DIGITACAO
        ), "Error with document workflow, state 'SITUACAO_EDOC_A_ENVIAR' "

        self.fiscal_document.action_document_confirm()
        self.fiscal_document._change_state(SITUACAO_EDOC_REJEITADA)

        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_REJEITADA
        ), "Error with document workflow, state 'SITUACAO_EDOC_REJEITADA' "

        self.fiscal_document.action_document_send()
        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_AUTORIZADA
        ), "Error with document workflow, state 'SITUACAO_EDOC_AUTORIZADA' "

    def test_no_electronic_01_draft_cancel(self):
        self.fiscal_document.document_electronic = False

        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_EM_DIGITACAO
        ), "Error with document workflow, state 'SITUACAO_EDOC_A_ENVIAR' "

        self.fiscal_document._document_cancel("Test")

        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_CANCELADA
        ), "Error with document workflow, state 'SITUACAO_EDOC_REJEITADA' "

    def test_electronic_01_draft_cancel(self):
        self.fiscal_document.document_electronic = True

        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_EM_DIGITACAO
        ), "Error with document workflow, state 'SITUACAO_EDOC_A_ENVIAR' "

        self.fiscal_document._document_cancel("Test")

        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_CANCELADA
        ), "Error with document workflow, state 'SITUACAO_EDOC_REJEITADA' "

    def test_electronic_01_back2draft(self):
        self.fiscal_document.document_electronic = True

        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_EM_DIGITACAO
        ), "Error with document workflow, state 'SITUACAO_EDOC_A_ENVIAR' "

        self.fiscal_document.action_document_confirm()
        self.fiscal_document.action_document_back2draft()

        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_EM_DIGITACAO
        ), "Error with document workflow, state 'SITUACAO_EDOC_A_ENVIAR' "

    def test_partner_issuer_confirm_idempotent(self):
        """
        Test that confirming a document with issuer='partner' multiple times
        does not raise an error. This is a regression test for a bug where
        action_document_confirm() would fail on the second call because
        the document was already in 'autorizada' state.

        The fix ensures _document_confirm_to_send() only processes documents
        in 'em_digitacao' state, making it safe to call multiple times.
        """
        self.fiscal_document.document_electronic = True
        self.fiscal_document.issuer = "partner"

        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_EM_DIGITACAO
        ), "Document should start in em_digitacao"

        # First confirm - should go directly to autorizada (issuer=partner)
        self.fiscal_document.action_document_confirm()
        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_AUTORIZADA
        ), "Document should be autorizada after first confirm"

        # Second confirm - should NOT raise error (idempotent behavior)
        # Before the fix, this would raise:
        # "Não é possível realizar esta operação, esta transição não é permitida:
        # De: autorizada Para: autorizada"
        self.fiscal_document.action_document_confirm()
        assert (
            self.fiscal_document.state_edoc == SITUACAO_EDOC_AUTORIZADA
        ), "Document should still be autorizada after second confirm"
