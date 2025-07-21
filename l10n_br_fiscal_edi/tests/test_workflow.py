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
