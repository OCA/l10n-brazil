# Copyright 2026 Pop Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from contextlib import contextmanager
from types import SimpleNamespace as NS
from unittest import mock

from odoo.tools import mute_logger

from odoo.addons.l10n_br_fiscal.constants.fiscal import PROCESSADOR_NENHUM

from ..models.document import _barueri_parse_mensagens, _cents, filter_oca_nfse
from .common import BarueriCommon, ok_line

RETORNO_OK = "1\r\n" + ok_line() + "\r\n9\r\n"


class FakeProcessador:
    """Barueri web service double: answers each operation from a list."""

    def __init__(self, answers):
        self._url = "https://testeeiss.barueri.sp.gov.br/"
        self.answers = answers
        self.calls = []
        self._transmissao = self

    @contextmanager
    def cliente(self, url):
        self.calls.append(url)
        yield NS(service=self)

    def __getitem__(self, operation):
        def call(version, message):
            self.calls.append((operation, message))
            answer = self.answers[operation]
            return answer.pop(0) if isinstance(answer, list) else answer

        return call


def _status(nome=None, situacao="2"):
    return NS(ListaNfeArquivosRPS=NS(SituacaoArq=situacao, NomeArqRetorno=nome))


class TestNFSeBarueriTransmission(BarueriCommon):
    def _processador(self, **answers):
        processador = FakeProcessador(answers)
        patcher = mock.patch.object(
            type(self.document),
            "_processador_erpbrasil_nfse",
            return_value=processador,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        return processador

    def _no_sleep(self):
        patcher = mock.patch("time.sleep")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_messages_of_the_answer_are_joined(self):
        lista = NS(
            MensagemRetorno=[
                NS(Codigo="OK200", Mensagem="Arquivo agendado", Correcao=None),
                NS(Codigo="R0001", Mensagem="Erro", Correcao="Corrija"),
            ]
        )
        self.assertEqual(
            _barueri_parse_mensagens(NS(ListaMensagemRetorno=lista)),
            "OK200 - Arquivo agendado\nR0001 - Erro - Correção: Corrija",
        )
        single = NS(Codigo="OK200", Mensagem="Ok", Correcao=None)
        self.assertEqual(
            _barueri_parse_mensagens(NS(ListaMensagemRetorno=single)), "OK200 - Ok"
        )
        self.assertEqual(_barueri_parse_mensagens(NS()), "")
        self.assertEqual(
            _barueri_parse_mensagens(NS(ListaMensagemRetorno=NS(Codigo=None))), ""
        )

    def test_an_invalid_amount_is_zero_cents(self):
        self.assertEqual(_cents("abc"), "0")
        self.assertEqual(_cents(None), "0")
        self.assertEqual(_cents(10.255), "1026")

    def test_send_is_authorized_from_the_return_file(self):
        self._no_sleep()
        processador = self._processador(
            NFeLoteEnviarArquivo=NS(
                ProtocoloRemessa="ENV123", ListaMensagemRetorno=None
            ),
            NFeLoteStatusArquivo=[_status(), _status("ENV123.RET")],
            # zeep may hand the base64Binary over still encoded
            NFeLoteBaixarArquivo=NS(
                ArquivoRPSBase64=base64.b64encode(RETORNO_OK.encode()).decode()
            ),
        )
        self.document.state_edoc = "enviada"
        self.document._barueri_process_send()
        self.assertEqual(self.document.state_edoc, "autorizada")
        self.assertEqual(self.document.document_number, "0000123")
        self.assertTrue(self.document.authorization_date)
        operations = [c[0] for c in processador.calls if isinstance(c, tuple)]
        self.assertEqual(
            operations,
            [
                "NFeLoteEnviarArquivo",
                "NFeLoteStatusArquivo",
                "NFeLoteStatusArquivo",
                "NFeLoteBaixarArquivo",
            ],
        )
        self.assertTrue(processador.calls[0].endswith("wsrps.asmx?WSDL"))

    def test_send_records_the_protocol_on_the_authorization_event(self):
        event = self.env["l10n_br_fiscal.event"].create_event_save_xml(
            company_id=self.company,
            environment="hml",
            event_type="0",
            xml_file="",
            document_id=self.document,
        )
        self.document.authorization_event_id = event
        self._processador(
            NFeLoteEnviarArquivo=NS(ProtocoloRemessa="ENV123"),
            NFeLoteStatusArquivo=_status("ENV123.RET"),
            NFeLoteBaixarArquivo=NS(ArquivoRPSBase64=RETORNO_OK.encode("latin-1")),
        )
        self.document.state_edoc = "enviada"
        with mock.patch.object(type(self.document), "_barueri_poll") as poll:
            poll.return_value = ("2", "ENV123.RET", RETORNO_OK)
            self.document._barueri_process_send()
        self.assertEqual(self.document.authorization_protocol, "ENV123")
        self.assertEqual(event.state, "done")
        self.assertEqual(self.document.state_edoc, "autorizada")

    def test_send_without_protocol_rejects_the_document(self):
        lista = NS(MensagemRetorno=[NS(Codigo="R0001", Mensagem="IM", Correcao="")])
        self._processador(
            NFeLoteEnviarArquivo=NS(ProtocoloRemessa=None, ListaMensagemRetorno=lista)
        )
        self.document.state_edoc = "enviada"
        self.document._barueri_process_send()
        self.assertEqual(self.document.state_edoc, "rejeitada")
        self.assertEqual(self.document.edoc_error_message, "R0001 - IM")

    def test_send_without_protocol_or_message(self):
        self._processador(NFeLoteEnviarArquivo=NS())
        self.document.state_edoc = "enviada"
        self.document._barueri_process_send()
        self.assertEqual(self.document.state_edoc, "rejeitada")
        self.assertTrue(self.document.edoc_error_message)

    @mute_logger("odoo.addons.l10n_br_nfse_barueri.models.document")
    def test_a_transmission_error_rejects_the_document(self):
        self.document.state_edoc = "enviada"
        with mock.patch.object(
            type(self.document),
            "_barueri_send_lote",
            side_effect=ConnectionError("timeout"),
        ):
            self.document._barueri_process_send()
        self.assertEqual(self.document.state_edoc, "rejeitada")
        self.assertEqual(self.document.edoc_error_message, "timeout")

    def test_poll_gives_up_without_return_file(self):
        self._no_sleep()
        self._processador(NFeLoteStatusArquivo=NS(ListaNfeArquivosRPS=None))
        self.assertEqual(
            self.document._barueri_poll("ENV123", tries=2, wait=0), (None, None, "")
        )

    def test_empty_return_file(self):
        processador = self._processador(NFeLoteBaixarArquivo=NS(ArquivoRPSBase64=None))
        self.assertEqual(
            self.document._barueri_baixa_retorno(processador, "1", "2", "X.RET"), ""
        )

    def test_error_return_rejects_the_document(self):
        retorno = "2RPS  ".ljust(1970) + "240;246;\r\n" + "texto sem codigo\r\n"
        self.document.state_edoc = "enviada"
        self.document._barueri_apply_result("ENV123", "OK200", "ENV123.ERR", retorno)
        self.assertEqual(self.document.state_edoc, "rejeitada")
        self.assertEqual(self.document.status_name, "Rejeitada (Registro 2: 240, 246)")
        self.document.state_edoc = "enviada"
        self.document._barueri_apply_result("ENV123", "", "ENV123.ERR", "")
        self.assertEqual(self.document.status_name, "Rejeitada (ver retorno)")

    def test_a_return_without_note_keeps_the_file_in_the_message(self):
        self.document.state_edoc = "enviada"
        self.document._barueri_apply_result("ENV123", "", "ENV123.RET", "9\r\n")
        self.assertEqual(self.document.state_edoc, "autorizada")
        self.assertIn("sem registro de NFS-e", self.document.edoc_error_message)

    @mute_logger("odoo.addons.l10n_br_nfse_barueri.models.document")
    def test_a_return_with_an_invalid_date(self):
        line = ok_line()
        line = line[:12] + "20261399" + line[20:]
        self.document.state_edoc = "enviada"
        self.document._barueri_apply_result("ENV123", "", "ENV.RET", "1\r\n" + line)
        self.assertEqual(self.document.state_edoc, "autorizada")
        self.assertEqual(self.document.document_number, "0000123")

    def test_status_reads_a_pending_remittance_again(self):
        self.document.state_edoc = "enviada"
        Document = type(self.document)
        with (
            mock.patch.object(
                Document,
                "authorization_protocol",
                new_callable=mock.PropertyMock,
                return_value="ENV123",
            ),
            mock.patch.object(
                Document, "_barueri_poll", return_value=("2", "ENV123.RET", RETORNO_OK)
            ) as poll,
        ):
            self.document._document_status()
        poll.assert_called_once_with("ENV123", tries=1, wait=0)
        self.assertEqual(self.document.state_edoc, "autorizada")
        with mock.patch.object(Document, "_barueri_poll") as poll:
            self.document._document_status()
        poll.assert_not_called()

    def test_serialize_gives_the_barueri_message(self):
        messages = [e for e in self.document.serialize() if isinstance(e, str)]
        self.assertEqual(len(messages), 1)
        self.assertTrue(messages[0].startswith("<NFeLoteEnviarArquivo"))
        self.assertIn("<InscricaoMunicipal>5366780</InscricaoMunicipal>", messages[0])

    def test_a_document_not_processed_by_oca_is_left_alone(self):
        self.company.processador_edoc = PROCESSADOR_NENHUM
        self.assertFalse(filter_oca_nfse(self.document))

    def test_record4_of_a_company_out_of_simples_nacional(self):
        record4 = self._rps_lines()[2]
        self.assertEqual(record4[1:3], "31")
        Document = type(self.document)
        original = Document._prepare_lote_rps

        def prepare_lote_rps(document):
            return dict(original(document), optante_simples_nacional="2")

        with mock.patch.object(Document, "_prepare_lote_rps", prepare_lote_rps):
            record4 = self._rps_lines()[2]
        self.assertEqual(record4[1:3], "10")

    def test_return_file_already_decoded(self):
        processador = self._processador(
            NFeLoteBaixarArquivo=NS(ArquivoRPSBase64="Lubrificação".encode())
        )
        self.assertEqual(
            self.document._barueri_baixa_retorno(processador, "1", "2", "X.RET"),
            "Lubrificação",
        )

    def test_error_lines_without_codes_are_skipped(self):
        self.assertEqual(self.document._barueri_erros_retorno("2RPS;ABC;\r\n"), [])

    def test_a_document_not_authorized_is_cancelled_as_usual(self):
        with mock.patch.object(type(self.document), "_trigger_fsm") as trigger:
            self.document._document_cancel("Servico nao prestado ao cliente")
        trigger.assert_called_once_with("action_cancel_fsm")

    def test_a_pending_return_moves_the_document_to_sent(self):
        self.document.state_edoc = "a_enviar"
        with mock.patch.object(type(self.document), "_barueri_process_send"):
            self.document._barueri_apply_result("ENV123", "", None, None)
        self.assertEqual(self.document.state_edoc, "enviada")

    def test_authorized_note_links_to_the_city_portal(self):
        self.document.partner_id.vat = "46.522.991/0001-73"
        self.assertFalse(self.document.url_nfse_barueri)
        self.document.verify_code = "886Q.0112.3910.1272299-V"
        self.document.nfse_environment = "2"
        url = self.document.url_nfse_barueri
        self.assertEqual(
            url,
            "https://testeeiss.barueri.sp.gov.br/nfe/wfimagemNota.aspx"
            "?CODIGOAUTENTICIDADE=886Q.0112.3910.1272299-V&NUMDOC=46522991000173",
        )
        action = self.document.action_open_nfse_barueri()
        self.assertEqual(action["url"], url)
        self.document.nfse_environment = "1"
        self.assertTrue(
            self.document.url_nfse_barueri.startswith("https://www.barueri.sp.gov.br")
        )

    def test_cron_reads_the_sent_notes_again(self):
        self.document.state_edoc = "enviada"
        Document = type(self.document)
        called = []

        def document_status(document):
            called.append(document.id)

        with mock.patch.object(Document, "_document_status", document_status):
            self.env[Document._name]._cron_document_status_barueri()
        self.assertEqual(called, [self.document.id])
