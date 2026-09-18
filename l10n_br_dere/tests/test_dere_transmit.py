# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import Mock, patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

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

    def _send_tables(self, declaration):
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

    def test_send_tables_with_http_mock(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1001")
        self.assertEqual(event.state, "sent")
        self.assertFalse(event.nr_recibo)
        self.assertEqual(event.protocol, "PROT-2026-0000000001")
        self.assertTrue(declaration.batch_ids)
        self.assertEqual(declaration.batch_ids.protocol, "PROT-2026-0000000001")
        self.assertNotIn("evtRetorno", declaration.batch_ids.protocol)
        self.assertTrue(declaration.can_consult_results)
        self._consult_results(declaration)
        self.assertFalse(declaration.can_consult_results)
        self.assertEqual(event.state, "accepted")
        self.assertEqual(event.nr_recibo, "REC-D1001-000000000000001")
        self.assertEqual(event.cd_retorno, "1")
        self.assertEqual(declaration.batch_ids.state, "done")

    def test_send_consults_the_batch_right_away(self):
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
            ),
        ):
            declaration.action_send_tables()
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1001")
        self.assertEqual(event.state, "accepted")
        self.assertEqual(declaration.batch_ids.state, "done")

    @mute_logger("odoo.addons.l10n_br_dere.models.dere_declaration")
    def test_send_survives_a_failing_consult(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        with (
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
                side_effect=self._fake_post,
            ),
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.get",
                side_effect=OSError("network down"),
            ),
        ):
            declaration.action_send_tables()
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1001")
        self.assertEqual(event.state, "sent")
        self.assertEqual(declaration.batch_ids.state, "sent")

    def test_consult_keeps_sent_while_processing(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        self._consult_results(
            declaration,
            get_side_effect=lambda url, **_kw: _FakeResponse(text=PROCESSING_LOTE),
        )
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1001")
        self.assertEqual(event.state, "sent")
        self.assertEqual(declaration.batch_ids.state, "sent")

    def test_cron_consult_applies_return(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        self._cron_consult()
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1001")
        self.assertEqual(event.state, "accepted")
        self.assertEqual(event.nr_recibo, "REC-D1001-000000000000001")
        self.assertEqual(declaration.batch_ids.state, "done")

    def test_cron_consult_keeps_sent_while_processing(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        self._cron_consult(
            get_side_effect=lambda url, **_kw: _FakeResponse(text=PROCESSING_LOTE),
        )
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1001")
        self.assertEqual(event.state, "sent")
        self.assertEqual(declaration.batch_ids.state, "sent")

    def test_cron_consult_http_error_does_not_fail(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        self._cron_consult(
            get_side_effect=lambda url, **_kw: _FakeResponse(
                status_code=503, text="unavailable"
            )
        )
        self.assertEqual(declaration.batch_ids.state, "sent")

    def test_consult_without_protocol(self):
        declaration = self._create_declaration()
        with self.assertRaises(UserError):
            declaration.action_consult_results()

    def test_consult_notifies_when_cron_already_processed_batch(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        self._cron_consult()
        self.assertEqual(declaration.batch_ids.state, "done")
        action = self._consult_results(declaration)
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["next"]["tag"], "soft_reload")

    def test_refuse_regenerate_after_accept(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._send_tables(declaration)
        self._consult_results(declaration)
        declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1011").write(
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
        with self.assertRaises(UserError):
            declaration._send_events(declaration.event_ids)

    def test_send_d1198_after_accepted_closing(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._post_entry("2026-10-10", self.receivable, self.fee_account, 50.0)
        declaration.action_generate_d1101()
        declaration.action_generate_d1199()
        self._accept_closing(declaration)
        declaration.action_mark_reopened()
        self.assertEqual(declaration.state, "closed")
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1198")
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
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1199")
        with self.assertRaises(UserError):
            declaration._send_events(event)

    def test_apply_return_occurrences(self):
        declaration = self._create_declaration()
        declaration.action_generate_d1001()
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1001")
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
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1001")
        self.assertNotIn("Signature", event.xml_content)
        self._send_tables(declaration)
        lote = declaration.batch_ids.xml_content
        self.assertIn("Signature", lote)
        self.assertIn("rsa-sha256", lote)
        self.assertIn("sha256", lote)
        self.assertIn(f'URI="#{event.event_id_attr}"', lote)
        self.assertNotIn("Signature", event.xml_content)
