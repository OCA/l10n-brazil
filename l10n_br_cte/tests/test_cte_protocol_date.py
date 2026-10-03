# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from types import SimpleNamespace
from unittest import mock

from odoo.tests import TransactionCase


class TestCTeProtocolDate(TransactionCase):
    """The date of the answer carries the local time with an offset.

    The Datetime fields keep naive UTC, so 10:15 at -03:00 is 13:15 and
    10:15 at -04:00 (MT, AM) is 14:15.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        company.processador_edoc = "oca"
        cls.cte = cls.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_57").id,
                "company_id": company.id,
                "document_number": "70001",
                "document_serie": "30",
                "document_date": datetime.now(),
                "cancel_reason": "Cancelamento de teste do CT-e.",
            }
        )

    def setUp(self):
        super().setUp()
        self.cte.authorization_event_id = self._event("0")
        self.cte.authorization_event_id.protocol_number = "135260000000001"

    def _event(self, event_type):
        return self.cte.event_ids.create_event_save_xml(
            company_id=self.cte.company_id,
            environment="hml",
            event_type=event_type,
            xml_file="<evento/>",
            document_id=self.cte,
        )

    def _event_answer(self, date):
        return SimpleNamespace(
            envio_xml="<evento/>",
            retorno=SimpleNamespace(content=b"<retorno/>"),
            resposta=SimpleNamespace(
                infEvento=SimpleNamespace(
                    cStat="135",
                    xMotivo="Evento registrado e vinculado ao CT-e",
                    chCTe=self.cte.document_key,
                    nProt="135260000000002",
                    dhRegEvento=date,
                )
            ),
        )

    def _processor(self, answer):
        processor = mock.MagicMock()
        processor.enviar_lote_evento.return_value = answer
        return mock.patch.object(
            type(self.cte), "_edoc_processor", return_value=processor
        )

    def test_authorization_protocol_date(self):
        for offset, expected in (
            ("-03:00", "2026-10-02 13:15:00"),
            ("-04:00", "2026-10-02 14:15:00"),
        ):
            with self.subTest(offset=offset):
                inf_prot = SimpleNamespace(
                    cStat="100",
                    xMotivo="Autorizado o uso do CT-e",
                    nProt="135260000000001",
                    dhRecbto="2026-10-02T10:15:00" + offset,
                )
                process = SimpleNamespace(
                    protocolo=SimpleNamespace(infProt=inf_prot),
                    processo_xml=b"<cteProc/>",
                )
                self.cte.state_edoc = "enviada"
                with mock.patch.object(type(self.cte), "_cte_response_add_proc"):
                    self.cte.update_status_cte(process)
                self.assertEqual(
                    str(self.cte.authorization_event_id.protocol_date), expected
                )

    def test_cancel_protocol_date(self):
        for offset, expected in (
            ("-03:00", "2026-10-02 13:15:00"),
            ("-04:00", "2026-10-02 14:15:00"),
        ):
            with self.subTest(offset=offset):
                answer = self._event_answer("2026-10-02T10:15:00" + offset)
                with self._processor(answer):
                    self.cte._cte_cancel()
                self.assertEqual(self.cte.cancel_event_id.state, "done")
                self.assertEqual(str(self.cte.cancel_event_id.protocol_date), expected)

    def test_correction_protocol_date(self):
        for offset, expected in (
            ("-03:00", "2026-10-02 13:15:00"),
            ("-04:00", "2026-10-02 14:15:00"),
        ):
            with self.subTest(offset=offset):
                answer = self._event_answer("2026-10-02T10:15:00" + offset)
                with self._processor(answer):
                    self.cte._cte_correction("Correcao de teste do CT-e.")
                event = self.cte.event_ids.filtered(lambda e: e.type == "14").sorted(
                    "id"
                )[-1]
                self.assertEqual(event.state, "done")
                self.assertEqual(str(event.protocol_date), expected)
