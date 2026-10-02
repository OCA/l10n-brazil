# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
from datetime import datetime
from io import BytesIO
from unittest import mock

from brazilfiscalreport.dacce import DaCCe
from erpbrasil.edoc.nfe import TEXTO_CARTA_CORRECAO
from lxml import etree, html

from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    SITUACAO_EDOC_AUTORIZADA,
)
from odoo.addons.l10n_br_fiscal_edi.constants.fiscal import CCE_CONDITION_OF_USE

from .mock_utils import load_soap_xml, nfe_mock
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


def _pdf_pages_text(pdf):
    """Text of each page of a PDF, with whichever reader the series ships."""
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfFileReader  # PyPDF2 1.x, shipped with Odoo 16

        reader = PdfFileReader(BytesIO(pdf))
        return [reader.getPage(index).extractText() for index in range(reader.numPages)]
    return [page.extract_text() for page in PdfReader(BytesIO(pdf)).pages]


def _pdf_text(pdf):
    return "\n".join(_pdf_pages_text(pdf))


def _proc_schema():
    import nfelib.nfe_evento_cce as cce

    path = os.path.join(
        os.path.dirname(cce.__file__), "schemas", "v1_0", "procCCeNFe_v1.00.xsd"
    )
    return etree.XMLSchema(etree.parse(path))


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
        self._add_event(nfe, 2, status_code="225")
        self._add_event(nfe, 3, state="draft")
        self._correct(nfe, VALID_TEXT)
        self.assertEqual(self._last_event(nfe).sequence, "2")

    @nfe_mock(CCE_REGISTERED)
    def test_duplicate_event_answer_consumes_the_sequence(self):
        """573 means the tax authority already has that number."""
        nfe = self._authorized_nfe()
        self._add_event(nfe, 1)
        self._add_event(nfe, 2, status_code="573")
        self._correct(nfe, VALID_TEXT)
        self.assertEqual(self._last_event(nfe).sequence, "3")

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

    @nfe_mock(CCE_REGISTERED)
    def test_registered_letter_is_stored_as_proc_evento(self):
        """The stored answer is the procEventoNFe, not the SOAP envelope."""
        nfe = self._authorized_nfe()
        self._correct(nfe, VALID_TEXT)
        event = self._last_event(nfe)
        proc = etree.fromstring(event.file_response_id.raw)
        self.assertEqual(etree.QName(proc).localname, "procEventoNFe")
        self.assertEqual(
            [etree.QName(child).localname for child in proc], ["evento", "retEvento"]
        )
        ns = {"n": NFE_NS}
        self.assertEqual(
            proc.findtext("n:retEvento/n:infEvento/n:nProt", namespaces=ns),
            event.protocol_number,
        )
        # the event is the signed one that was sent
        self.assertEqual(
            etree.tostring(proc.find("n:evento/n:infEvento", ns), method="c14n"),
            etree.tostring(
                self._request_xml(event).find(".//n:infEvento", ns), method="c14n"
            ),
        )
        _proc_schema().assertValid(proc)

    @nfe_mock(CCE_REGISTERED)
    def test_registration_date_is_stored_in_utc(self):
        """dhRegEvento 16:52:52-03:00 is 19:52:52 UTC."""
        nfe = self._authorized_nfe()
        self._correct(nfe, VALID_TEXT)
        self.assertEqual(
            self._last_event(nfe).protocol_date, datetime(2023, 7, 5, 19, 52, 52)
        )

    @nfe_mock(CCE_REFUSED)
    def test_refused_letter_keeps_the_soap_answer(self):
        """There is no procEventoNFe for an event that was not registered."""
        nfe = self._authorized_nfe()
        self._correct(nfe, VALID_TEXT)
        answer = etree.fromstring(self._last_event(nfe).file_response_id.raw)
        self.assertEqual(etree.QName(answer).localname, "Envelope")

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
        new_bodies = [
            str(m.body) for m in nfe.message_ids[: len(nfe.message_ids) - messages]
        ]
        self.assertTrue(
            any("refused" in body and "225" in body for body in new_bodies),
            new_bodies,
        )

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

    @nfe_mock(CCE_REFUSED)
    def test_print_menu_of_a_refused_letter_is_blocked(self):
        """The Print menu of the event list does not go through the button."""
        nfe = self._authorized_nfe()
        self._correct(nfe, VALID_TEXT)
        event = self._last_event(nfe)
        self.assertFalse(event.can_print)
        report = self.env["ir.actions.report"]
        with self.assertRaises(UserError):
            report._render_qweb_html(
                "l10n_br_fiscal_edi.action_report_document_event", event.ids
            )

    @nfe_mock(CCE_REGISTERED)
    def test_only_registered_letter_can_be_printed(self):
        nfe = self._authorized_nfe()
        draft = self._add_event(nfe, 1, state="draft")
        with self.assertRaises(UserError):
            draft.print_document_event()
        self._correct(nfe, VALID_TEXT)
        registered = self._last_event(nfe)
        self.assertTrue(registered.can_print)
        self.assertTrue(registered.print_document_event())

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

    # -- DACCE (printing with BrazilFiscalReport) --------------------------

    EVENT_REPORT = "l10n_br_fiscal_edi.main_report_document_event"

    def _render_event_pdf(self, *events):
        events = events[0].browse([event.id for event in events])
        return events.env["ir.actions.report"]._render_qweb_pdf(
            self.EVENT_REPORT, events.ids
        )

    @nfe_mock(CCE_REGISTERED)
    def test_registered_letter_is_printed_by_the_dacce_library(self):
        nfe = self._authorized_nfe()
        self._correct(nfe, VALID_TEXT)
        event = self._last_event(nfe)
        with mock.patch(
            "odoo.addons.l10n_br_nfe.report.ir_actions_report.DaCCe",
            wraps=DaCCe,
        ) as dacce:
            pdf, fmt = self._render_event_pdf(event)
        dacce.assert_called_once()
        self.assertEqual(fmt, "pdf")
        self.assertTrue(pdf.startswith(b"%PDF"))
        text = _pdf_text(pdf)
        key = nfe.document_key
        for expected in (
            " ".join(key[i : i + 4] for i in range(0, 44, 4)),
            event.protocol_number,
            event.document_id.company_id.partner_id.legal_name,
            VALID_TEXT,
            "CORRE",  # the heading of the corrections box
        ):
            self.assertIn(expected, text)

    @nfe_mock(CCE_REGISTERED)
    def test_dacce_prints_the_local_registration_time_of_the_xml(self):
        """16:52:52 is the time in the XML (-03:00), whatever the user timezone."""
        nfe = self._authorized_nfe()
        self._correct(nfe, VALID_TEXT)
        event = self._last_event(nfe)
        for tz in ("Europe/Brussels", "UTC", "America/Sao_Paulo"):
            text = _pdf_text(self._render_event_pdf(event.with_context(tz=tz))[0])
            self.assertIn("05/07/2023 16:52:52", text)

    @nfe_mock(CCE_REGISTERED)
    def test_dacce_marks_the_homologation_environment(self):
        nfe = self._authorized_nfe()
        self._correct(nfe, VALID_TEXT)
        event = self._last_event(nfe)
        self.assertEqual(event.environment, EVENT_ENV_HML)
        self.assertIn("SEM VALOR FISCAL", _pdf_text(self._render_event_pdf(event)[0]))
        event.environment = "prod"
        self.assertNotIn(
            "SEM VALOR FISCAL", _pdf_text(self._render_event_pdf(event)[0])
        )

    @nfe_mock(CCE_REGISTERED)
    def test_event_without_proc_evento_does_not_use_the_library(self):
        """Letters stored before the procEventoNFe was kept have the SOAP answer."""
        nfe = self._authorized_nfe()
        event = self._add_event(nfe, 1)
        self.assertFalse(event._get_proc_evento_nfe())
        with mock.patch(
            "odoo.addons.l10n_br_nfe.report.ir_actions_report.DaCCe"
        ) as dacce:
            self._render_event_pdf(event)
        dacce.assert_not_called()

    @nfe_mock(CCE_REGISTERED)
    def test_unregistered_letter_cannot_be_rendered(self):
        """The print menu of the event goes straight to the report."""
        nfe = self._authorized_nfe()
        draft = self._add_event(nfe, 1, state="draft")
        with self.assertRaises(UserError):
            self._render_event_pdf(draft)
        refused = self._add_event(nfe, 2, status_code="573")
        with self.assertRaises(UserError):
            self._render_event_pdf(refused)

    @nfe_mock(CCE_REGISTERED)
    def test_several_letters_make_one_pdf(self):
        nfe = self._authorized_nfe()
        self._correct(nfe, VALID_TEXT)
        first = self._last_event(nfe)
        self._correct(nfe, VALID_TEXT)
        second = self._last_event(nfe)
        self.assertNotEqual(first, second)
        self.assertEqual(
            len(_pdf_pages_text(self._render_event_pdf(first, second)[0])), 2
        )

    @nfe_mock(CCE_REGISTERED)
    def test_pdf_name_has_the_key_and_the_sequence(self):
        nfe = self._authorized_nfe()
        self._correct(nfe, VALID_TEXT)
        event = self._last_event(nfe)
        report = self.env.ref("l10n_br_fiscal_edi.action_report_document_event")
        self.assertEqual(
            safe_eval(report.print_report_name, {"object": event}),
            f"CCe-{nfe.document_key}-{event.sequence}",
        )

    # -- QWeb report: the fallback of the DACCE ----------------------------

    def _old_style_letter(self, nfe):
        """A registered letter as it was stored before the procEventoNFe:
        the answer is the SOAP envelope, and protocol_date has the old bug.
        """
        self._correct(nfe, VALID_TEXT + "\nSecond line of the correction")
        event = self._last_event(nfe)
        event.file_response_id.raw = load_soap_xml(
            "retEnvEvento/nfe_cce_registrada.xml"
        )
        event.protocol_date = datetime(2023, 7, 5, 16, 52, 52)
        self.assertFalse(event._get_proc_evento_nfe())
        return event

    def _event_html(self, event):
        content = event.env["ir.actions.report"]._render_qweb_html(
            self.EVENT_REPORT, event.ids
        )[0]
        return html.fromstring(content)

    @staticmethod
    def _html_text(tree):
        return " ".join(tree.text_content().split())

    def test_condition_of_use_is_a_literal_of_the_schema(self):
        ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
        literals = _cce_xsd().xpath(
            "//xs:element[@name='xCondUso']//xs:enumeration/@value", namespaces=ns
        )
        self.assertIn(CCE_CONDITION_OF_USE, literals)
        # and it is the one that the library sends in the event
        self.assertEqual(CCE_CONDITION_OF_USE, TEXTO_CARTA_CORRECAO)

    @nfe_mock(CCE_REGISTERED)
    def test_fallback_prints_the_condition_of_use_of_the_schema(self):
        nfe = self._authorized_nfe()
        event = self._old_style_letter(nfe)
        text = self._html_text(self._event_html(event))
        self.assertIn(CCE_CONDITION_OF_USE, text)
        # the fixed text that was in the template is gone
        self.assertNotIn("não seja relacionado", text)

    @nfe_mock(CCE_REGISTERED)
    def test_fallback_has_the_data_of_a_correction_letter(self):
        nfe = self._authorized_nfe()
        event = self._old_style_letter(nfe)
        text = self._html_text(self._event_html(event))
        company = nfe.company_id.partner_id
        recipient = nfe.partner_id
        key = nfe.document_key
        for expected in (
            company.legal_name,
            company.vat,
            company.l10n_br_ie_code,
            recipient.legal_name or recipient.name,
            recipient.vat,
            " ".join(key[i : i + 4] for i in range(0, 44, 4)),
            f"ID110110{key}01",
            "135 - Evento registrado e vinculado a NF-e",
            "141190000382704",
            VALID_TEXT,
            "Second line of the correction",
        ):
            self.assertIn(expected, text)
        self.assertTrue(company.vat and recipient.vat)

    @nfe_mock(CCE_REGISTERED)
    def test_fallback_keeps_the_line_breaks_of_the_correction(self):
        nfe = self._authorized_nfe()
        event = self._old_style_letter(nfe)
        event.justification = "First line of the text\nSecond line of the text"
        tree = self._event_html(event)
        node = tree.xpath("//div[contains(@style, 'pre-line')]")[0]
        self.assertEqual(
            node.text_content(), "First line of the text\nSecond line of the text"
        )
        # the literal \n that the library used to send also breaks the line
        event.justification = "First line of the text\\nSecond line of the text"
        node = self._event_html(event).xpath("//div[contains(@style, 'pre-line')]")[0]
        self.assertEqual(
            node.text_content(), "First line of the text\nSecond line of the text"
        )

    @nfe_mock(CCE_REGISTERED)
    def test_fallback_registration_time_comes_from_the_xml(self):
        """protocol_date of an old letter is wrong (the bug fixed for new ones)."""
        nfe = self._authorized_nfe()
        event = self._old_style_letter(nfe)
        self.assertIn(
            "05/07/2023 16:52:52 (UTC-03:00)",
            self._html_text(self._event_html(event)),
        )

    @nfe_mock(CCE_REGISTERED)
    def test_fallback_without_xml_converts_protocol_date_to_brasilia(self):
        nfe = self._authorized_nfe()
        event = self._old_style_letter(nfe)
        event.file_response_id.unlink()
        event.protocol_date = datetime(2026, 10, 2, 13, 15, 0)
        for tz in ("UTC", "Europe/Brussels"):
            text = self._html_text(self._event_html(event.with_context(tz=tz)))
            self.assertIn("02/10/2026 10:15:00 (UTC-03:00)", text)

    @nfe_mock(CCE_REGISTERED)
    def test_fallback_marks_the_homologation_environment(self):
        nfe = self._authorized_nfe()
        event = self._old_style_letter(nfe)
        self.assertEqual(event.environment, EVENT_ENV_HML)
        self.assertTrue(self._event_html(event).xpath("//div[@class='watermark']"))
        event.environment = "prod"
        self.assertFalse(self._event_html(event).xpath("//div[@class='watermark']"))

    @nfe_mock(CCE_REGISTERED)
    def test_fallback_labels_are_translated_to_portuguese(self):
        self.env["res.lang"]._activate_lang("pt_BR")
        self.env["ir.module.module"].search(
            [("name", "=", "l10n_br_fiscal_edi")]
        )._update_translations(["pt_BR"])
        nfe = self._authorized_nfe()
        event = self._old_style_letter(nfe)
        text = self._html_text(self._event_html(event))
        for expected in (
            "Emitente",
            "Destinatário",
            "Chave de acesso",
            "Correções a serem consideradas",
            "Representação gráfica de CC-e",
            "Registrado em:",
        ):
            self.assertIn(expected, text)
        self.assertNotIn("Recipient", text)
