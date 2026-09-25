# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import Mock, patch

import requests

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_dere.models import xml_builder

from .common import DereCommon

RETURN_D9001 = """<?xml version="1.0" encoding="utf-8"?>
<DeRE xmlns="http://www.dere.gov.br/schemas/evtRetornoTabela/v1_0_1">
  <evtRetornoTabela>
    <ideStatus>
      <cdRetorno>1</cdRetorno>
      <descRetorno>Sucesso</descRetorno>
    </ideStatus>
    <infoRecEv>
      <nrRecibo>REC-D1001-000000000000001</nrRecibo>
      <protocoloLote>PROT-2026-0000000001</protocoloLote>
      <dhRecepcao>2026-10-16T12:00:00Z</dhRecepcao>
      <dhProcess>2026-10-16T12:00:01Z</dhProcess>
      <tpEv>D-1001</tpEv>
      <hash>abcd</hash>
    </infoRecEv>
  </evtRetornoTabela>
</DeRE>
"""

RETURN_D1198 = """<?xml version="1.0" encoding="utf-8"?>
<DeRE xmlns="http://www.dere.gov.br/schemas/evtRetornoReabert/v0_0_1">
  <evtRetornoReabert>
    <ideStatus>
      <cdRetorno>1</cdRetorno>
      <descRetorno>Sucesso</descRetorno>
    </ideStatus>
    <infoRecEv>
      <nrRecibo>1198-202610-0000000000000000001</nrRecibo>
      <protocoloLote>PROT-2026-0000000002</protocoloLote>
      <tpEv>D-1198</tpEv>
    </infoRecEv>
  </evtRetornoReabert>
</DeRE>
"""

PROCESSING_LOTE = """<?xml version="1.0" encoding="utf-8"?>
<DeRE xmlns="http://www.dere.gov.br/schemas/retornoLoteDere/v1_0_1">
  <retornoLoteEventos>
    <status>
      <cdResposta>1</cdResposta>
      <descResposta>Waiting</descResposta>
    </status>
    <dadosRecepcaoLote>
      <protocolo>PROT-2026-0000000001</protocolo>
    </dadosRecepcaoLote>
  </retornoLoteEventos>
</DeRE>
"""


class _FakeResponse:
    def __init__(self, status_code=200, text="", payload=None):
        self.status_code = status_code
        self.text = text
        self._payload = payload or {}

    def json(self):
        return self._payload


@tagged("post_install", "-at_install")
class TestDereTransmit(DereCommon):
    def _fake_post(self, url, **_kwargs):
        if "token" in url:
            return _FakeResponse(
                payload={"access_token": "demo-token", "expires_in": 3600}
            )
        return _FakeResponse(
            text='{"protocolo": "PROT-2026-0000000001"}',
            payload={"protocolo": "PROT-2026-0000000001"},
        )

    def _fake_get(self, url, **_kwargs):
        return _FakeResponse(text=RETURN_D9001)

    def _processing_get(self, url, **_kwargs):
        return _FakeResponse(text=PROCESSING_LOTE)

    def _table_batches(self, declaration):
        return self._table_period(declaration).batch_ids

    def _make_batch_due(self, declaration):
        batches = self._table_batches(declaration) | declaration.batch_ids
        batches.write({"next_consult_at": False})

    def _send_tables(self, declaration):
        with patch(
            "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
            side_effect=self._fake_post,
        ):
            declaration.action_send_tables()

    def _consult_results(self, declaration, get_side_effect=None):
        with (
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
                side_effect=self._fake_post,
            ),
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.get",
                side_effect=get_side_effect or self._fake_get,
            ),
        ):
            return declaration.action_consult_results()

    def _cron_consult(self, get_side_effect=None):
        with (
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
                side_effect=self._fake_post,
            ),
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.get",
                side_effect=get_side_effect or self._fake_get,
            ),
        ):
            self.env["l10n_br_dere.batch"]._cron_consult_batches()

    def test_parse_return_keeps_receipt_and_protocol_apart(self):
        parsed = xml_builder.parse_return(RETURN_D9001)
        self.assertEqual(parsed["cdRetorno"], "1")
        self.assertEqual(parsed["nrRecibo"], "REC-D1001-000000000000001")
        self.assertEqual(parsed["protocoloLote"], "PROT-2026-0000000001")
        self.assertEqual(parsed["tpEv"], "D-1001")

    def test_parse_return_ignores_extract_receipts(self):
        extract = """
    <extratoEventos>
      <detEvento>
        <nrRecibo>REC-D1001-OLDER</nrRecibo>
        <iniValid>2026-01-01</iniValid>
      </detEvento>
      <detEvento>
        <nrRecibo>REC-D1001-NEWER</nrRecibo>
        <iniValid>2026-10-01</iniValid>
      </detEvento>
    </extratoEventos>
  </evtRetornoTabela>"""
        parsed = xml_builder.parse_return(
            RETURN_D9001.replace("\n  </evtRetornoTabela>", extract)
        )
        self.assertEqual(parsed["nrRecibo"], "REC-D1001-000000000000001")
        self.assertEqual(parsed["events"][0]["nrRecibo"], "REC-D1001-000000000000001")

    def test_send_tables_with_http_mock(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        event = self._event(declaration, "D-1001")
        batch = self._table_batches(declaration)
        self.assertEqual(event.state, "sent")
        self.assertFalse(event.nr_recibo)
        self.assertEqual(event.protocol, "PROT-2026-0000000001")
        self.assertTrue(batch)
        self.assertEqual(batch.protocol, "PROT-2026-0000000001")
        self.assertNotIn("evtRetorno", batch.protocol)
        self.assertTrue(batch.next_consult_at)
        self.assertTrue(declaration.can_consult_results)
        self._consult_results(declaration)
        self.assertFalse(declaration.can_consult_results)
        self.assertEqual(event.state, "accepted")
        self.assertEqual(event.nr_recibo, "REC-D1001-000000000000001")
        self.assertEqual(event.cd_retorno, "1")
        self.assertEqual(batch.state, "done")

    def test_send_does_not_consult_immediately(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        with (
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
                side_effect=self._fake_post,
            ),
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.get",
                side_effect=self._fake_get,
            ) as mocked_get,
        ):
            declaration.action_send_tables()
        event = self._event(declaration, "D-1001")
        self.assertEqual(event.state, "sent")
        self.assertEqual(self._table_batches(declaration).state, "sent")
        mocked_get.assert_not_called()

    def test_send_timeout_keeps_unknown_batch(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        period = self._table_period(declaration)
        events = period._next_events(("D-1001",))
        self.assertTrue(events)
        with patch.object(
            type(self.env["l10n_br_dere.receita.integra"]),
            "send_batch",
            side_effect=requests.Timeout("timed out"),
        ):
            action = period._send_events(events)
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(period.batch_ids.state, "unknown")
        self.assertEqual(events.state, "generated")

    def test_send_without_protocol_keeps_unknown_batch(self):
        declaration = self._create_declaration("2025-03")
        declaration.action_generate_tables()
        period = self._table_period(declaration)
        events = period._next_events(("D-1001",))
        with patch.object(
            type(self.env["l10n_br_dere.receita.integra"]),
            "send_batch",
            return_value={"ok": True, "status_code": 200, "text": "accepted"},
        ):
            action = period._send_events(events)
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(period.batch_ids.state, "unknown")
        self.assertFalse(period.batch_ids.protocol)
        self.assertEqual(events.state, "generated")

    def test_send_application_error_rejects_events(self):
        declaration = self._create_declaration("2025-05")
        declaration.action_generate_tables()
        period = self._table_period(declaration)
        events = period._next_events(("D-1001",))
        with patch.object(
            type(self.env["l10n_br_dere.receita.integra"]),
            "send_batch",
            return_value={
                "ok": False,
                "status_code": 400,
                "text": "batch rejected",
            },
        ):
            action = period._send_events(events)
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(period.batch_ids.state, "error")
        self.assertEqual(events.state, "rejected")

    def test_send_transient_http_keeps_generated_events(self):
        declaration = self._create_declaration("2025-04")
        declaration.action_generate_tables()
        period = self._table_period(declaration)
        events = period._next_events(("D-1001",))
        with patch.object(
            type(self.env["l10n_br_dere.receita.integra"]),
            "send_batch",
            return_value={
                "ok": False,
                "status_code": 503,
                "text": "unavailable",
            },
        ):
            action = period._send_events(events)
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(period.batch_ids.state, "unknown")
        self.assertEqual(events.state, "generated")

    def test_consult_keeps_sent_while_processing(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        self._consult_results(
            declaration,
            get_side_effect=lambda url, **_kw: _FakeResponse(text=PROCESSING_LOTE),
        )
        event = self._event(declaration, "D-1001")
        self.assertEqual(event.state, "sent")
        self.assertEqual(self._table_batches(declaration).state, "sent")

    def test_cron_consult_applies_return(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        self._make_batch_due(declaration)
        self._cron_consult()
        event = self._event(declaration, "D-1001")
        self.assertEqual(event.state, "accepted")
        self.assertEqual(event.nr_recibo, "REC-D1001-000000000000001")
        self.assertEqual(self._table_batches(declaration).state, "done")

    def test_cron_consult_skips_batches_that_are_not_due(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        self._cron_consult()
        event = self._event(declaration, "D-1001")
        self.assertEqual(event.state, "sent")
        self.assertEqual(self._table_batches(declaration).state, "sent")

    def test_cron_consult_keeps_sent_while_processing(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        self._make_batch_due(declaration)
        self._cron_consult(
            get_side_effect=lambda url, **_kw: _FakeResponse(text=PROCESSING_LOTE),
        )
        event = self._event(declaration, "D-1001")
        self.assertEqual(event.state, "sent")
        self.assertEqual(self._table_batches(declaration).state, "sent")

    def test_cron_consult_http_error_does_not_fail(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        self._make_batch_due(declaration)
        self._cron_consult(
            get_side_effect=lambda url, **_kw: _FakeResponse(
                status_code=503, text="unavailable"
            )
        )
        self.assertEqual(self._table_batches(declaration).state, "sent")

    def test_consult_without_protocol(self):
        declaration = self._create_declaration()
        with self.assertRaises(UserError):
            declaration.action_consult_results()

    def test_consult_notifies_when_cron_already_processed_batch(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        self._make_batch_due(declaration)
        self._cron_consult()
        self.assertEqual(self._table_batches(declaration).state, "done")
        action = self._consult_results(declaration)
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["next"]["tag"], "soft_reload")

    def test_refuse_regenerate_after_accept(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        self._consult_results(declaration)
        self._event(declaration, "D-1011").write(
            {"state": "accepted", "cd_retorno": "1"}
        )
        self.assertFalse(declaration.can_generate_tables)
        self.assertFalse(declaration.can_send_tables)
        with self.assertRaises(UserError):
            declaration.action_generate_tables()

    def test_refuse_mixed_table_and_periodic_batch(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._post_entry("2026-10-10", self.receivable, self.fee_account, 50.0)
        declaration.action_generate_d1101()
        mixed = self._table_period(declaration).event_ids | declaration.event_ids
        with self.assertRaises(UserError):
            declaration._send_events(mixed)

    def test_send_d1198_after_accepted_closing(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._post_entry("2026-10-10", self.receivable, self.fee_account, 50.0)
        declaration.action_generate_d1101()
        declaration.action_generate_d1199()
        self._accept_closing(declaration)
        declaration.action_mark_reopened()
        self.assertEqual(declaration.state, "closed")
        event = self._event(declaration, "D-1198")
        with (
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
                side_effect=self._fake_post,
            ),
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.get",
                side_effect=self._processing_get,
            ),
        ):
            declaration.action_send_periodics()
        self.assertEqual(event.state, "sent")
        self.assertIn("evtReabertMensal", declaration.batch_ids[:1].xml_content)
        self._consult_results(
            declaration,
            get_side_effect=lambda url, **_kw: _FakeResponse(text=RETURN_D1198),
        )
        self.assertEqual(event.state, "accepted")
        self.assertEqual(event.nr_recibo, "1198-202610-0000000000000000001")
        self.assertEqual(declaration.state, "reopened")

    def test_d1199_send_requires_d1101_receipt(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._post_entry("2026-10-10", self.receivable, self.fee_account, 50.0)
        declaration.action_generate_d1101()
        declaration.action_generate_d1199()
        event = self._event(declaration, "D-1199")
        with self.assertRaises(UserError):
            declaration._send_events(event)

    def test_apply_return_occurrences(self):
        declaration = self._create_declaration()
        declaration.action_generate_d1001()
        event = self._event(declaration, "D-1001")
        declaration.apply_return(
            event,
            "0",
            desc_retorno="Erro",
            occurrences=[
                {
                    "codigo": "12",
                    "descricao": "Invalid activity",
                    "tipo": "1",
                    "localizacao": "plAssistSaude",
                }
            ],
        )
        self.assertEqual(event.state, "rejected")
        self.assertEqual(event.occurrence_ids.codigo, "12")

    def test_missing_credentials(self):
        self.company.dere_client_id = False
        declaration = self._create_declaration()
        declaration.action_generate_d1001()
        with patch(
            "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
            return_value=Mock(),
        ) as mocked:
            with self.assertRaises(UserError):
                declaration.action_send_tables()
            mocked.assert_not_called()

    def test_send_signs_event_with_sha256(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        event = self._event(declaration, "D-1001")
        self.assertNotIn("Signature", event.xml_content)
        self._send_tables(declaration)
        lote = self._table_batches(declaration).xml_content
        self.assertIn("Signature", lote)
        self.assertIn("rsa-sha256", lote)
        self.assertIn("sha256", lote)
        self.assertIn(f'URI="#{event.event_id_attr}"', lote)
        self.assertNotIn("Signature", event.xml_content)

    def test_send_accepts_plain_text_protocol(self):
        declaration = self._create_declaration("2025-01")
        declaration.action_generate_tables()

        def fake_post(url, **_kwargs):
            if "token" in url:
                return _FakeResponse(
                    payload={"access_token": "demo-token", "expires_in": 3600}
                )
            return _FakeResponse(text="2.000001.123456")

        with patch(
            "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
            side_effect=fake_post,
        ):
            declaration.action_send_tables()
        self.assertEqual(self._table_batches(declaration).protocol, "2.000001.123456")

    def test_consult_rejects_events_on_lot_error(self):
        declaration = self._create_declaration("2025-02")
        declaration.action_generate_tables()
        self._send_tables(declaration)
        rejected = """<?xml version="1.0" encoding="utf-8"?>
<DeRE xmlns="http://www.dere.gov.br/schemas/retornoLoteDere/v1_0_1">
  <retornoLoteEventos>
    <status>
      <cdResposta>7</cdResposta>
      <descResposta>Schema error</descResposta>
      <ocorrencias>
        <ocorrencia>
          <codigo>MS1050</codigo>
          <descricao>Invalid event id</descricao>
          <tipo>1</tipo>
        </ocorrencia>
      </ocorrencias>
    </status>
  </retornoLoteEventos>
</DeRE>
"""
        self._consult_results(
            declaration,
            get_side_effect=lambda url, **_kw: _FakeResponse(text=rejected),
        )
        event = self._event(declaration, "D-1001")
        self.assertEqual(event.state, "rejected")
        self.assertEqual(event.occurrence_ids.codigo, "MS1050")
        self.assertEqual(self._table_batches(declaration).state, "error")

    def test_parse_return_matches_lot_events_by_id(self):
        parsed = xml_builder.parse_return(
            """<?xml version="1.0" encoding="utf-8"?>
<DeRE xmlns="http://www.dere.gov.br/schemas/retornoLoteDere/v1_0_1">
  <retornoLoteEventos>
    <status>
      <cdResposta>2</cdResposta>
      <descResposta>Done</descResposta>
    </status>
    <retornoEventos>
      <evento id="DeRE100110000001234567820260101000001">
        <evtRetornoTabela>
          <ideStatus>
            <cdRetorno>1</cdRetorno>
            <descRetorno>Sucesso</descRetorno>
          </ideStatus>
          <infoRecEv>
            <nrRecibo>REC-LOT-1</nrRecibo>
            <tpEv>D-1001</tpEv>
          </infoRecEv>
        </evtRetornoTabela>
      </evento>
    </retornoEventos>
  </retornoLoteEventos>
</DeRE>
"""
        )
        self.assertEqual(parsed["cdResposta"], "2")
        self.assertEqual(len(parsed["events"]), 1)
        self.assertEqual(
            parsed["events"][0]["id"],
            "DeRE100110000001234567820260101000001",
        )
        self.assertEqual(parsed["events"][0]["nrRecibo"], "REC-LOT-1")
