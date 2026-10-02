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
        # a refused letter cannot be printed as if it was valid
        with self.assertRaises(UserError):
            event.print_document_event()

    @nfe_mock(CCE_REGISTERED)
    def test_only_registered_letter_can_be_printed(self):
        nfe = self._authorized_nfe()
        draft = self._add_event(nfe, 1, state="draft")
        with self.assertRaises(UserError):
            draft.print_document_event()
        self._correct(nfe, VALID_TEXT)
        self.assertTrue(self._last_event(nfe).print_document_event())

    # -- text --------------------------------------------------------------

    @nfe_mock(CCE_REGISTERED)
    def test_pasted_text_is_normalized_and_valid_in_the_schema(self):
        nfe = self._authorized_nfe()
        ldq, rdq, dash, dots = "\U0000201c", "\U0000201d", "\U00002013", "\U00002026"
        pasted = (
            f"  Onde se lê {ldq}transportadora X{rdq} {dash} leia{dash}se Y{dots}"
            "\n\tvolumes:   2\r\n"
        )
        self._correct(nfe, pasted)
        event = self._last_event(nfe)
        expected = 'Onde se lê "transportadora X" - leia-se Y... volumes: 2'
        self.assertEqual(event.justification, expected)
        self.assertIn(expected, nfe.correction_reason)
        request = self._request_xml(event)
        det = request.find(f".//{{{NFE_NS}}}detEvento")
        self.assertEqual(det.findtext(f"{{{NFE_NS}}}xCorrecao"), expected)
        schema = _cce_schema()
        schema.assertValid(etree.fromstring(etree.tostring(det)))

    def test_raw_pasted_text_would_not_pass_the_schema(self):
        """Guard for the test above: the schema does refuse what we clean."""
        schema = _cce_schema()
        ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
        cond_use = _cce_xsd().xpath(
            "//xs:element[@name='xCondUso']//xs:enumeration/@value", namespaces=ns
        )[1]

        def det(text):
            root = etree.Element(f"{{{NFE_NS}}}detEvento", versao="1.00")
            etree.SubElement(root, f"{{{NFE_NS}}}descEvento").text = "Carta de Correcao"
            etree.SubElement(root, f"{{{NFE_NS}}}xCorrecao").text = text
            etree.SubElement(root, f"{{{NFE_NS}}}xCondUso").text = cond_use
            return root

        self.assertTrue(schema.validate(det(VALID_TEXT)))
        for bad in (
            "valid text \u201cquoted\u201d here",
            "valid text \u2013 dash here",
            "valid text\u2026 here ok",
            "valid\ttext with tab",
            "valid text with trailing space ",
        ):
            self.assertFalse(schema.validate(det(bad)), repr(bad))

    @nfe_mock(CCE_REGISTERED)
    def test_invalid_text_is_refused_before_sending(self):
        nfe = self._authorized_nfe()
        count = len(nfe.event_ids)
        for text in (
            "",
            "   \n ",
            "short text",
            "x" * 1001,
            "valid text with emoji \U0001f600",
        ):
            with (
                mock.patch(
                    "nfelib.nfe.ws.edoc_legacy.NFeAdapter.enviar_lote_evento"
                ) as send,
                self.assertRaises(UserError, msg=repr(text)),
            ):
                self._correct(nfe, text)
            send.assert_not_called()
        self.assertEqual(len(nfe.event_ids), count)

    # -- NFC-e -------------------------------------------------------------

    @nfe_mock(SEND_MOCKS)
    def test_nfce_does_not_accept_correction_letter(self):
        nfe = self._authorized_nfe()
        nfce = self.env.ref("l10n_br_fiscal.document_65")
        nfe.document_type_id = nfce
        with self.assertRaises(UserError):
            nfe.action_document_correction()
