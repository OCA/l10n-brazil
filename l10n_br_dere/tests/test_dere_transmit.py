# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import Mock, patch

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
        return _FakeResponse(text=RETURN_D9001)

    def test_parse_return_keeps_receipt_and_protocol_apart(self):
        parsed = xml_builder.parse_return(RETURN_D9001)
        self.assertEqual(parsed["cdRetorno"], "1")
        self.assertEqual(parsed["nrRecibo"], "REC-D1001-000000000000001")
        self.assertEqual(parsed["protocoloLote"], "PROT-2026-0000000001")
        self.assertEqual(parsed["tpEv"], "D-1001")

    def test_send_tables_with_http_mock(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        with patch(
            "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
            side_effect=self._fake_post,
        ):
            declaration.action_send_tables()
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1001")
        self.assertEqual(event.state, "accepted")
        self.assertEqual(event.nr_recibo, "REC-D1001-000000000000001")
        self.assertEqual(event.protocol, "PROT-2026-0000000001")
        self.assertEqual(event.cd_retorno, "1")
        self.assertTrue(declaration.batch_ids)

    def test_refuse_mixed_table_and_periodic_batch(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._post_entry("2026-10-10", self.receivable, self.fee_account, 50.0)
        declaration.action_generate_d1101()
        with self.assertRaises(UserError):
            declaration._send_events(declaration.event_ids)

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
