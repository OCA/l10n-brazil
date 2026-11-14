# Copyright 2026 KMEE (Luis Felipe Mileo <mileo@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Conservative coverage of the legacy erpbrasil.edoc transmission.

The ``test_nfe_webservices.py``, ``test_nfce.py`` and ``test_nfe_workflow.py``
files are the REFERENCE tests: they run with the nfelib SOAP transmission
(the stack meant to survive). This module reruns those reference classes
with the legacy erpbrasil.edoc stack (``l10n_br_nfe.nfelib_soap_transmission``
forced to ``False``), so a regression of the legacy path is caught even
while nfelib is the tested default of this branch.

The SAME ``nfe_mock`` helper and the SAME XML fixtures drive both stacks:
``NFeMock`` patches the nfelib xsdata transport and the legacy
``erpbrasil.transmissao`` layer at once and only the stack selected by the
config parameter is exercised.

These classes are plain subclasses of the reference ones on purpose: when
the erpbrasil.edoc transmission is dropped (planned on the 20.0 branch),
deleting this whole file restores a pure nfelib test suite.
"""

from unittest import mock

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_REJEITADA,
)
from odoo.addons.l10n_br_nfe.models.document import NFe

from . import test_nfce, test_nfe_webservices, test_nfe_workflow
from .mock_utils import NFeEdocLegacyMixin, nfe_mock
from .test_nfe_serialize import TestNFeExport
from .test_nfe_workflow import NFE_LC_DEMO, RecordingNFeMock


class TestNFeWebServicesLegacyEdoc(
    NFeEdocLegacyMixin, test_nfe_webservices.TestNFeWebServices
):
    """test_nfe_webservices scenarios over the legacy erpbrasil.edoc stack."""


class TestNFCeLegacyEdoc(NFeEdocLegacyMixin, test_nfce.TestNFCe):
    """test_nfce scenarios over the legacy erpbrasil.edoc stack."""


class TestNFeWorkflowRejectionLegacyEdoc(
    NFeEdocLegacyMixin, test_nfe_workflow.TestNFeWorkflowRejection
):
    """Rejection -> correction -> resend over the legacy stack."""


class TestNFeWorkflowDenialLegacyEdoc(
    NFeEdocLegacyMixin, test_nfe_workflow.TestNFeWorkflowDenial
):
    """Denial (denegada) of an own NF-e over the legacy stack."""


class TestNFeWorkflowBack2DraftLegacyEdoc(
    NFeEdocLegacyMixin, test_nfe_workflow.TestNFeWorkflowBack2Draft
):
    """back2draft from every reachable state over the legacy stack."""


class TestNFeWorkflowAsyncLegacyEdoc(NFeEdocLegacyMixin, TestNFeExport):
    """The asynchronous NF-e flow (send, then receipt consult) over the
    legacy erpbrasil.edoc stack."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass(nfe_list=[{"record_ref": NFE_LC_DEMO}])
        cls.nfe = cls.nfe_list[0]["nfe"]

    def _send_async(self):
        # NOTE: the flag is read on self.env.company, see the reference
        # TestNFeWorkflowAsync tests.
        self.env.company.nfe_separate_async_process = True
        nfe = self.nfe_list[0]["nfe"]
        self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_A_ENVIAR)
        with mock.patch.object(NFe, "make_pdf"):
            nfe.action_document_send()
        # Sent, but the receipt has not been consulted: no protocol yet.
        self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_ENVIADA)
        self.assertFalse(nfe.authorization_protocol)

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
        }
    )
    def test_async_send_then_consult_receipt_authorizes(self):
        self._send_async()

        self.nfe._nfe_consult_receipt()

        self.assertEqual(self.nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertTrue(self.nfe.authorization_protocol)

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/uso_denegado.xml",
        }
    )
    def test_async_receipt_consult_returning_denial(self):
        self._send_async()

        self.nfe._nfe_consult_receipt()

        self.assertEqual(self.nfe.state_edoc, SITUACAO_EDOC_DENEGADA)
        self.assertEqual(self.nfe.status_code, "303")

    def test_async_send_without_mock_fails_fast(self):
        """Sanity: without a SEFAZ mock the legacy stack must not silently
        authorize (proves these tests really go through the legacy code)."""
        recorder = RecordingNFeMock({})
        with recorder, self.assertRaises(Exception):  # noqa: B017
            self._send_async()
        self.assertIn("nfeAutorizacaoLote", recorder.legacy_calls)
        self.assertEqual(recorder.calls, [])
        self.assertNotEqual(self.nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)


class TestNFeRejectRoundTripLegacyEdoc(NFeEdocLegacyMixin, TestNFeExport):
    """Rejection round trips over the legacy stack."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass(nfe_list=[{"record_ref": NFE_LC_DEMO}])
        cls.nfe = cls.nfe_list[0]["nfe"]

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/rejeitada.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
        }
    )
    def test_rejection_back2draft_resend_roundtrip(self):
        """reject -> back2draft -> confirm -> reject again stays consistent."""
        for _ in range(2):
            self.assertEqual(self.nfe.state_edoc, SITUACAO_EDOC_A_ENVIAR)
            self.nfe.action_document_send()
            self.assertEqual(self.nfe.state_edoc, SITUACAO_EDOC_REJEITADA)

            self.nfe.action_document_back2draft()
            self.assertEqual(self.nfe.state_edoc, SITUACAO_EDOC_EM_DIGITACAO)

            self.nfe.action_document_confirm()
            self.assertEqual(self.nfe.state_edoc, SITUACAO_EDOC_A_ENVIAR)

        self.assertEqual(self.nfe.status_code, "225")
        self.assertEqual(self.nfe.status_name, "Rejeicao: Falha no Schema XML da NFe")
