# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    PROCESSADOR_NENHUM,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_EM_DIGITACAO,
)
from odoo.addons.l10n_br_fiscal_edi.constants.fiscal import DOCUMENT_STATE_SENDING
from odoo.addons.queue_job.tests.common import trap_jobs


@tagged("post_install", "-at_install")
class TestFiscalQueue(TransactionCase):
    """Envio assincrono via queue_job.

    O documento usa um tipo eletronico proprio do teste, que nenhum modulo de
    transmissao reconhece, e a empresa fica sem processador de documentos.
    Assim o envio cai na implementacao base do l10n_br_fiscal_edi, que apenas
    leva o documento a AUTORIZADA (sem tocar a SEFAZ), mesmo com l10n_br_nfe e
    afins instalados. Isso torna os testes do split (send_now x with_delay)
    deterministicos e independentes de rede.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.operation_model = cls.env["l10n_br_fiscal.operation"]
        cls.document_model = cls.env["l10n_br_fiscal.document"]
        cls.env.company.processador_edoc = PROCESSADOR_NENHUM
        cls.document_type = cls.env["l10n_br_fiscal.document.type"].create(
            {
                "code": "QUEUE",
                "name": "Fiscal queue test",
                "type": "icms",
                "electronic": True,
            }
        )

        cls.operation_now = cls.operation_model.create(
            {
                "name": "Venda sincrona",
                "code": "QUEUE-NOW",
                "fiscal_operation_type": "out",
                "queue_document_send": "send_now",
            }
        )
        cls.operation_later = cls.operation_model.create(
            {
                "name": "Venda assincrona",
                "code": "QUEUE-LATER",
                "fiscal_operation_type": "out",
                "queue_document_send": "with_delay",
            }
        )

    def _new_document(self, operation):
        return self.document_model.create(
            {
                "document_type_id": self.document_type.id,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": operation.id,
            }
        )

    def _confirm(self, document):
        self.assertEqual(document.state_edoc, SITUACAO_EDOC_EM_DIGITACAO)
        document.action_document_confirm()
        self.assertEqual(document.state_edoc, SITUACAO_EDOC_A_ENVIAR)

    def test_operation_default_is_send_now(self):
        operation = self.operation_model.create(
            {
                "name": "Sem config de fila",
                "code": "QUEUE-DEF",
                "fiscal_operation_type": "out",
            }
        )
        self.assertEqual(operation.queue_document_send, "send_now")

    def test_send_now_is_synchronous(self):
        document = self._new_document(self.operation_now)
        self._confirm(document)
        with trap_jobs() as trap:
            document.action_document_send()
            trap.assert_jobs_count(0)
        # o envio sincrono levou o documento direto a autorizada
        self.assertEqual(document.state_edoc, SITUACAO_EDOC_AUTORIZADA)

    def test_with_delay_enqueues_job(self):
        document = self._new_document(self.operation_later)
        self._confirm(document)
        with trap_jobs() as trap:
            document.action_document_send()
            trap.assert_jobs_count(1)
            trap.assert_enqueued_job(document._job_document_send)
            # enquanto o job nao roda, o documento segue aguardando envio
            self.assertEqual(document.state_edoc, SITUACAO_EDOC_A_ENVIAR)
            # ao processar a fila, a transmissao real acontece
            trap.perform_enqueued_jobs()
        self.assertEqual(document.state_edoc, SITUACAO_EDOC_AUTORIZADA)

    def test_mixed_batch_splits_by_operation(self):
        # o envio (action_document_send) opera sobre o recordset, e e nesse
        # ponto que o split por operacao acontece
        document_now = self._new_document(self.operation_now)
        document_later = self._new_document(self.operation_later)
        self._confirm(document_now)
        self._confirm(document_later)
        batch = document_now | document_later
        with trap_jobs() as trap:
            batch.action_document_send()
            # apenas o with_delay foi enfileirado
            trap.assert_jobs_count(1)
            trap.assert_enqueued_job(document_later._job_document_send)
        # o send_now ja autorizou sincronamente; o with_delay ainda aguarda
        self.assertEqual(document_now.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(document_later.state_edoc, SITUACAO_EDOC_A_ENVIAR)

    def test_job_skips_a_document_no_longer_waiting(self):
        """The job does not transmit a document sent while it waited."""
        document = self._new_document(self.operation_later)
        self._confirm(document)
        with trap_jobs() as trap:
            document.action_document_send()
            trap.assert_jobs_count(1)
            # someone sends it right away while the job is still queued
            document.with_context(
                l10n_br_fiscal_queue_send_now=True
            ).action_document_send()
            self.assertEqual(document.state_edoc, SITUACAO_EDOC_AUTORIZADA)
            self.assertFalse(document._job_document_send())
        self.assertEqual(document.state_edoc, SITUACAO_EDOC_AUTORIZADA)

    def test_job_transmits_a_document_in_the_sending_state(self):
        """The job resends a document still waiting for processing."""
        document = self._new_document(self.operation_later)
        self._confirm(document)
        # action_send also accepts the sending state (resend or receipt
        # consult of an asynchronous batch)
        document.state_edoc = DOCUMENT_STATE_SENDING
        with trap_jobs() as trap:
            document.action_document_send()
            trap.assert_jobs_count(1)
            trap.assert_enqueued_job(document._job_document_send)
            self.assertEqual(document.state_edoc, DOCUMENT_STATE_SENDING)
            trap.perform_enqueued_jobs()
        # the job went through the transmission instead of skipping it
        self.assertEqual(document.state_edoc, SITUACAO_EDOC_AUTORIZADA)

    def test_job_skips_documents_that_cannot_be_sent(self):
        """Draft, authorized and cancelled documents are still ignored."""
        for state in (
            SITUACAO_EDOC_EM_DIGITACAO,
            SITUACAO_EDOC_AUTORIZADA,
            SITUACAO_EDOC_CANCELADA,
        ):
            document = self._new_document(self.operation_later)
            document.state_edoc = state
            self.assertFalse(document._job_document_send())
            self.assertEqual(document.state_edoc, state)
