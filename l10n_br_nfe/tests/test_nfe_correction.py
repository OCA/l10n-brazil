# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
from unittest import mock

from lxml import etree

from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    SITUACAO_EDOC_AUTORIZADA,
)

from .mock_utils import nfe_mock
from .test_nfe_serialize import TestNFeExport

NFE_NS = "http://www.portalfiscal.inf.br/nfe"
SEND_MOCKS = {
    "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
    "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
}
CCE_REGISTERED = {
    **SEND_MOCKS,
    "nfeRecepcaoEvento": "retEnvEvento/nfe_cce_registrada.xml",
}
CCE_REFUSED = {**SEND_MOCKS, "nfeRecepcaoEvento": "retEnvEvento/nfe_cce_rejeitada.xml"}
CCE_BATCH_REFUSED = {
    **SEND_MOCKS,
    "nfeRecepcaoEvento": "retEnvEvento/nfe_cce_lote_rejeitado.xml",
}
VALID_TEXT = "Onde se le transportadora X, leia-se transportadora Y"


def _cce_xsd():
    import nfelib.nfe_evento_cce as cce

    path = os.path.join(
        os.path.dirname(cce.__file__), "schemas", "v1_0", "e110110_v1.00.xsd"
    )
    return etree.parse(path)


def _cce_schema():
    return etree.XMLSchema(_cce_xsd())


class TestNFeCorrection(TestNFeExport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass(
            [
                {
                    "record_ref": "l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11",
                    "xml_file": "NFe35200159594315000157550010000000022062777169.xml",
                },
            ]
        )

    def _authorized_nfe(self):
        nfe = self.nfe_list[0]["nfe"]
        nfe.action_document_send()
        self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        return nfe

    def _add_event(self, nfe, sequence, status_code="135", state="done"):
        event = nfe.event_ids.create_event_save_xml(
            company_id=nfe.company_id,
            environment=EVENT_ENV_HML,
            event_type="14",
            xml_file="<evento/>",
            document_id=nfe,
            sequence=str(sequence),
            justification=VALID_TEXT,
        )
        if state == "done":
            event.set_done(status_code, "mocked", False, "1" + str(sequence), False)
        return event

    def _correct(self, nfe, text):
        wizard = (
            self.env["l10n_br_fiscal.document.correction.wizard"]
            .with_context(active_model="l10n_br_fiscal.document", active_id=nfe.id)
            .create({"document_id": nfe.id, "justification": text})
        )
        return wizard.doit()

    def _last_event(self, nfe):
        return nfe.event_ids.filtered(lambda e: e.type == "14").sorted("id")[-1]

    @staticmethod
    def _request_xml(event):
        return etree.fromstring(event.file_request_id.raw)

    # -- sequence ----------------------------------------------------------

    @nfe_mock(CCE_REGISTERED)
    def test_eleventh_letter_gets_sequence_eleven(self):
        """The sequence is text: the maximum of "1".."10" is "9" as text."""
        nfe = self._authorized_nfe()
        for number in range(1, 11):
            self._add_event(nfe, number)
        self._correct(nfe, VALID_TEXT)
        event = self._last_event(nfe)
        self.assertEqual(event.sequence, "11")
        request = self._request_xml(event)
        self.assertEqual(
            request.findtext(f".//{{{NFE_NS}}}nSeqEvento"),
            "11",
        )

    @nfe_mock(CCE_REGISTERED)
    def test_first_letter_gets_sequence_one(self):
        nfe = self._authorized_nfe()
        self._correct(nfe, VALID_TEXT)
        self.assertEqual(self._last_event(nfe).sequence, "1")

    @nfe_mock(CCE_REGISTERED)
    def test_refused_letters_do_not_consume_the_sequence(self):
        nfe = self._authorized_nfe()
        self._add_event(nfe, 1)
        self._add_event(nfe, 2, status_code="573")
        self._add_event(nfe, 3, state="draft")
        self._correct(nfe, VALID_TEXT)
        self.assertEqual(self._last_event(nfe).sequence, "2")

    @nfe_mock(CCE_REGISTERED)
    def test_twenty_one_letters_are_refused_before_sending(self):
        nfe = self._authorized_nfe()
        for number in range(1, 21):
            self._add_event(nfe, number)
        count = len(nfe.event_ids)
        with (
            mock.patch(
                "nfelib.nfe.ws.edoc_legacy.NFeAdapter.enviar_lote_evento"
            ) as send,
            self.assertRaises(UserError),
        ):
            self._correct(nfe, VALID_TEXT)
        send.assert_not_called()
        self.assertEqual(len(nfe.event_ids), count)

    # -- answers of the tax authority --------------------------------------

    @nfe_mock(CCE_REGISTERED)
    def test_registered_letter(self):
        nfe = self._authorized_nfe()
        action = self._correct(nfe, VALID_TEXT)
        event = self._last_event(nfe)
        self.assertEqual(event.state, "done")
        self.assertEqual(event.status_code, "135")
        self.assertEqual(event.protocol_number, "141190000382704")
        self.assertEqual(action["params"]["type"], "success")

    @nfe_mock(CCE_BATCH_REFUSED)
    def test_refused_batch_is_recorded_and_visible(self):
        """No per event answer: the cStat of the batch must reach the user."""
        nfe = self._authorized_nfe()
        messages = len(nfe.message_ids)
        action = self._correct(nfe, VALID_TEXT)
        event = self._last_event(nfe)
        self.assertEqual(event.status_code, "225")
        self.assertIn("Falha no Schema", event.response)
        self.assertEqual(event.state, "done")
        self.assertTrue(event.file_request_id)
        self.assertTrue(event.file_response_id)
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["type"], "danger")
        self.assertIn("225", action["params"]["message"])
        self.assertGreater(len(nfe.message_ids), messages)
        self.assertIn("225", nfe.message_ids[0].body)

    @nfe_mock(CCE_REFUSED)
    def test_refused_event_keeps_event_and_xml(self):
        nfe = self._authorized_nfe()
        count = len(nfe.event_ids)
        action = self._correct(nfe, VALID_TEXT)
        self.assertEqual(len(nfe.event_ids), count + 1)
        event = self._last_event(nfe)
        self.assertEqual(event.status_code, "573")
        self.assertIn("Duplicidade", event.response)
        self.assertTrue(event.file_request_id.raw)
        self.assertIn("573", action["params"]["message"])
