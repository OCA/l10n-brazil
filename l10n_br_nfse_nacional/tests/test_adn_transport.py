# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import gzip
from unittest import mock

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.l10n_br_nfse_nacional.transport.adn_rest import (
    AdnRestClient,
)


def _fake_response(status_code=200, payload=None, content=b""):
    """Build a requests.Response-like mock for the ADN client."""
    resp = mock.Mock()
    resp.status_code = status_code
    resp.content = content
    if payload is None:
        resp.json.side_effect = ValueError("no json body")
    else:
        resp.json.return_value = payload
    return resp


@tagged("post_install", "-at_install")
class TestAdnTransport(TransactionCase):
    """Unit tests for the REST/mTLS ADN client, fully mocked (no network)."""

    def _client(self):
        return AdnRestClient(
            "https://sefin.example.gov.br/SefinNacional", "/tmp/fake-cert.pem"
        )

    def test_pack_dps_roundtrip(self):
        xml = "<DPS><infDPS/></DPS>"
        packed = AdnRestClient.pack_dps(xml)
        back = gzip.decompress(base64.b64decode(packed)).decode("utf-8")
        self.assertEqual(back, xml)

    def test_tls_verification_always_on(self):
        client = self._client()
        self.assertIs(client._session.verify, True)

    def test_post_dps_authorized(self):
        client = self._client()
        body = {"chaveAcesso": "5" * 50, "nNFSe": "123", "protocolo": "PROT1"}
        with mock.patch.object(
            client._session, "post", return_value=_fake_response(200, body)
        ) as posted:
            resp = client.post_dps("Zm9v")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.body["chaveAcesso"], "5" * 50)
        posted.assert_called_once()
        self.assertTrue(posted.call_args.args[0].endswith("/nfse"))

    def test_post_dps_rejection_without_json(self):
        client = self._client()
        with mock.patch.object(
            client._session,
            "post",
            return_value=_fake_response(400, payload=None, content=b"bad request"),
        ):
            resp = client.post_dps("Zm9v")
        self.assertEqual(resp.status_code, 400)
        self.assertIsNone(resp.body)
        self.assertEqual(resp.content, b"bad request")

    def test_get_nfse_reconcile(self):
        client = self._client()
        with mock.patch.object(
            client._session, "get", return_value=_fake_response(200, {"ok": True})
        ) as got:
            client.get_nfse("5" * 50)
        got.assert_called_once()
        self.assertTrue(got.call_args.args[0].endswith("/nfse/" + "5" * 50))

    def test_get_event_found(self):
        client = self._client()
        with mock.patch.object(
            client._session, "get", return_value=_fake_response(200, {"ok": True})
        ) as got:
            resp = client.get_event("5" * 50, "101101", "1")
        got.assert_called_once()
        self.assertTrue(
            got.call_args.args[0].endswith("/nfse/" + "5" * 50 + "/eventos/101101/1")
        )
        self.assertEqual(resp.status_code, 200)

    def test_get_event_not_found(self):
        client = self._client()
        with mock.patch.object(
            client._session,
            "get",
            return_value=_fake_response(404, payload=None, content=b"not found"),
        ):
            resp = client.get_event("5" * 50, "305101", "1")
        self.assertEqual(resp.status_code, 404)
