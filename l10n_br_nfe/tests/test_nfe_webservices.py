# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# Copyright (C) 2024 - TODAY Antônio S. P. Neto - Engenere
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import logging
from unittest import mock

from odoo.exceptions import UserError
from odoo.fields import Datetime

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_INUTILIZADA,
)
from odoo.addons.l10n_br_nfe.models.document import NFe

from .mock_utils import nfe_mock
from .test_nfe_serialize import TestNFeExport

_logger = logging.getLogger(__name__)


class TestNFeWebServices(TestNFeExport):
    @classmethod
    def setUpClass(cls):
        nfe_list = [
            {
                "record_ref": "l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11",
                "xml_file": "NFe35200159594315000157550010000000022062777169.xml",
            },
        ]
        super().setUpClass(nfe_list)

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
            "nfeRecepcaoEvento": "retEnvEvento/nfe_cancelamento.xml",
        }
    )
    def test_enviar_e_cancelar(self):
        for nfe_data in self.nfe_list:
            nfe = nfe_data["nfe"]

            nfe.action_document_send()

            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)

            cancel_wizard = (
                self.env["l10n_br_fiscal.document.cancel.wizard"]
                .with_context(active_model="l10n_br_fiscal.document", active_id=nfe.id)
                .create(
                    {"document_id": nfe.id, "justification": "Era apenas um teste."}
                )
            )
            cancel_wizard.doit()

            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_CANCELADA)
            self.assertIsNotNone(nfe.cancel_event_id)
            self.assertEqual(nfe.cancel_event_id.state, "done")
            self.assertEqual(nfe.cancel_event_id.status_code, "135")
            self.assertEqual(
                nfe.cancel_event_id.response, "Evento registrado e vinculado a NF-e"
            )
            self.assertEqual(
                Datetime.to_string(nfe.cancel_event_id.protocol_date),
                "2023-07-05 16:52:52",
            )

    @nfe_mock({"nfeInutilizacaoNF": "retInutNFe/nfe_inutilizacao.xml"})
    def test_inutilizar(self):
        nfe = self.nfe_list[0]["nfe"]
        inutilizar_wizard = (
            self.env["l10n_br_fiscal.invalidate.number.wizard"]
            .with_context(active_model="l10n_br_fiscal.document", active_id=nfe.id)
            .create({"document_id": nfe.id, "justification": "Era apenas um teste."})
        )
        inutilizar_wizard.doit()

    def _create_invalidate_number(self, number_start, number_end):
        nfe = self.nfe_list[0]["nfe"]
        return self.env["l10n_br_fiscal.invalidate.number"].create(
            {
                "company_id": nfe.company_id.id,
                "document_type_id": nfe.document_type_id.id,
                "document_serie_id": nfe.document_serie_id.id,
                "number_start": number_start,
                "number_end": number_end,
                "justification": "Era apenas um teste.",
            }
        )

    @nfe_mock({"nfeInutilizacaoNF": "retInutNFe/nfe_inutilizacao.xml"})
    def test_inutilizar_range_with_existing_document(self):
        """A range with a number already used by a document is refused before
        reaching the tax authority, instead of failing afterwards on the
        document number constraint (which rolls back the Odoo record while the
        number stays invalidated at the tax authority)."""
        nfe = self.nfe_list[0]["nfe"]
        number = int(nfe.document_number)
        invalidate = self._create_invalidate_number(number - 1, number + 1)
        model = type(invalidate)
        with (
            mock.patch.object(
                model,
                "_edoc_processor",
                autospec=True,
                side_effect=model._edoc_processor,
            ) as processor,
            self.assertRaises(UserError) as error,
        ):
            invalidate.action_invalidate()
        processor.assert_not_called()
        self.assertIn("already fiscal documents", error.exception.args[0])
        self.assertIn(str(number), error.exception.args[0])
        self.assertEqual(invalidate.state, "draft")

    @nfe_mock({"nfeInutilizacaoNF": "retInutNFe/nfe_inutilizacao.xml"})
    def test_inutilizar_range_without_existing_document(self):
        nfe = self.nfe_list[0]["nfe"]
        number = int(nfe.document_number) + 5000
        invalidate = self._create_invalidate_number(number, number + 1)
        invalidate.action_invalidate()
        self.assertEqual(invalidate.state, "done")
        documents = self.env["l10n_br_fiscal.document"].search(
            [
                ("document_serie_id", "=", nfe.document_serie_id.id),
                ("document_number", "in", [str(number), str(number + 1)]),
            ]
        )
        self.assertEqual(len(documents), 2)
        self.assertEqual(
            documents.mapped("state_edoc"), [SITUACAO_EDOC_INUTILIZADA] * 2
        )

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
        }
    )
    def test_nfe_consult_receipt(self):
        """
        Tests the asynchronous NFe transmission, separating the sending and
        the consultation into two distinct steps.
        """
        for nfe_data in self.nfe_list:
            nfe = nfe_data["nfe"]
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_A_ENVIAR)
            with mock.patch.object(NFe, "make_pdf"):
                # enable skip receipt consultation during the send action
                self.env.company.nfe_separate_async_process = True
                nfe.action_document_send()
            # Document has been sent, but the receipt has not been consulted yet,
            # meaning the authorization protocol has not been received.
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_ENVIADA)
            # Consult the receipt to receive the usage authorization.
            nfe._nfe_consult_receipt()
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
        }
    )
    @mock.patch("odoo.addons.l10n_br_nfe.models.document._logger")
    def test_nfe_consult_receipt_without_nfe_saved(self, mock_logger):
        """
        Tests the NF-e processing result query after deleting the sent nfe xml.
        """
        for nfe_data in self.nfe_list:
            nfe = nfe_data["nfe"]
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_A_ENVIAR)
            with mock.patch.object(NFe, "make_pdf"):
                # enable skip receipt consultation during the send action
                self.env.company.nfe_separate_async_process = True
                nfe.action_document_send()
            # Document has been sent, but the receipt has not been consulted yet,
            # meaning the authorization protocol has not been received.
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_ENVIADA)
            # Consult the receipt to receive the usage authorization.

            # Erase the sending_file
            nfe.send_file_id = False
            self.assertFalse(nfe.send_file_id)

            nfe._nfe_consult_receipt()
            mock_logger.info.assert_called_with(
                "NF-e data not found when trying to assemble the "
                "xml with the authorization protocol (nfeProc)"
            )
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)

    @nfe_mock({"nfeConsultaNF": "retConsSitNFe/autorizado.xml"})
    def test_nfe_consult(self):
        for nfe_data in self.nfe_list:
            nfe = nfe_data["nfe"]
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_A_ENVIAR)
            nfe._document_status()
            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)
