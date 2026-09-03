# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import re
from unittest import mock

import requests

from odoo.tests.common import TransactionCase, tagged

SIGN_XML = "nfelib.CommonMixin.sign_xml"
SCHEMA_VALIDATION = (
    "odoo.addons.l10n_br_nfse_nacional.models.document.Dps.schema_validation"
)
SESSION_POST = "requests.Session.post"

AUTHORIZED = {
    "chaveAcesso": "5" * 50,
    "nNFSe": "123",
    "protocolo": "PROT-1",
    "motivo": "Autorizado",
}
REJECTED = {"erros": [{"codigo": "E0001", "descricao": "Documento inválido"}]}
CANCELLED = {"mensagem": "Cancelado", "protocolo": "PROT-CANC"}


def mock_response(body, status_code=200):
    resp = mock.MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.json.return_value = body
    resp.content = json.dumps(body).encode()
    return resp


@tagged("post_install", "-at_install")
class TestNfseLifecycle(TransactionCase):
    """Issuance and cancellation lifecycle with the ADN transport mocked."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.doc = cls.env.ref(
            "l10n_br_nfse_nacional.demo_nfse_lc", raise_if_not_found=False
        )
        if not cls.doc:
            return
        company = cls.doc.company_id
        company.write(
            {
                "processador_edoc": "oca",
                "provedor_nfse": False,
                "nfse_environment": "2",
            }
        )
        serie = cls.env["l10n_br_fiscal.document.serie"].search(
            [
                ("document_type_id", "=", cls.doc.document_type_id.id),
                ("company_id", "=", company.id),
            ],
            limit=1,
        )
        if not serie:
            serie = cls.env["l10n_br_fiscal.document.serie"].create(
                {
                    "name": "NFS-e Nacional",
                    "code": "1",
                    "document_type_id": cls.doc.document_type_id.id,
                    "company_id": company.id,
                }
            )
        cls.doc.document_serie_id = serie.id

    def setUp(self):
        super().setUp()
        if not self.doc:
            self.skipTest("l10n_br_nfse_nacional demo data is not installed")
        for target, value in ((SIGN_XML, "<x>signed</x>"), (SCHEMA_VALIDATION, [])):
            patcher = mock.patch(target, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_issuance_authorized(self):
        with mock.patch(SESSION_POST, return_value=mock_response(AUTHORIZED)):
            self.doc.action_document_confirm()
            self.doc.action_document_send()
        self.assertEqual(self.doc.state_edoc, "autorizada")
        self.assertEqual(self.doc.nfse_key, "5" * 50)
        self.assertEqual(self.doc.nfse_number, "123")
        self.assertEqual(self.doc.nfse_protocol, "PROT-1")
        self.assertFalse(self.doc.edoc_error_message)
        self.assertEqual(self.doc.authorization_event_id.state, "done")

    def test_issuance_rejected(self):
        with mock.patch(SESSION_POST, return_value=mock_response(REJECTED, 400)):
            self.doc.action_document_confirm()
            self.doc.action_document_send()
        self.assertEqual(self.doc.state_edoc, "rejeitada")
        self.assertIn("E0001", self.doc.edoc_error_message or "")
        self.assertFalse(self.doc.nfse_key)

    def test_cancel_event_id_layout(self):
        self.doc.nfse_key = "5" * 50
        event_id = self.doc._cancel_event_id()
        self.assertEqual(len(event_id), 59)
        self.assertTrue(re.fullmatch(r"PRE[0-9]{56}", event_id))
        self.assertEqual(event_id, "PRE" + "5" * 50 + "101101")

    def test_cancel_pedreg_omits_npedregevento(self):
        self.doc.nfse_key = "5" * 50
        ped = self.doc._build_cancel_pedreg("Erro na emissao do documento.", "1")
        self.assertFalse(ped.infPedReg.nPedRegEvento)
        self.assertNotIn("nPedRegEvento", self.doc._serialize_pedreg(ped))

    def test_cancellation(self):
        self.doc.nfse_key = "5" * 50
        with mock.patch(SESSION_POST, return_value=mock_response(CANCELLED)):
            self.doc._adn_cancel("Erro na emissão do documento.", "1")
        self.assertTrue(self.doc.cancel_event_id)
        self.assertEqual(self.doc.cancel_event_id.state, "done")
        self.assertEqual(self.doc.cancel_event_id.type, "2")

    def test_check_status_detects_oficio_cancellation(self):
        self.doc.nfse_key = "5" * 50
        self.doc.state_edoc = "autorizada"
        event_body = {"eventoXmlGZipB64": ""}
        responses = {
            "101101": mock_response({}, 404),
            "305101": mock_response(event_body, 200),
        }

        def fake_get(url, timeout=None):
            tipo = "101101" if "/101101/" in url else "305101"
            return responses[tipo]

        with mock.patch("requests.Session.get", side_effect=fake_get):
            self.doc.action_adn_check_status()
        self.assertEqual(self.doc.state_edoc, "cancelada")
        self.assertTrue(self.doc.cancel_event_id)
        self.assertEqual(self.doc.cancel_event_id.state, "done")

    def test_check_status_no_cancellation_found(self):
        self.doc.nfse_key = "5" * 50
        self.doc.state_edoc = "autorizada"
        with mock.patch("requests.Session.get", return_value=mock_response({}, 404)):
            self.doc.action_adn_check_status()
        self.assertEqual(self.doc.state_edoc, "autorizada")
        self.assertFalse(self.doc.cancel_event_id)
