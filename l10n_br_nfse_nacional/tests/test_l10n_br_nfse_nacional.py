# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests import common

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFSE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_REJEITADA,
)

from ..constants.nfse_nacional import ADN_URL, DANFSE_URL
from ..models.document import filter_processador_nfse_nacional

_PATCH_API = "odoo.addons.l10n_br_nfse_nacional.models.document.Document._api_request"
_PATCH_PAYLOAD = (
    "odoo.addons.l10n_br_nfse_nacional.models.document.Document._prepare_dps_payload"
)


def _mock_response(status_code, json_data=None, content=b""):
    """Build a mock requests.Response with fixed status_code, json body and content."""
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data or {}
    r.content = content
    return r


def _authorized_json(chave="A" * 44, numero="999"):
    return {
        "status": "autorizado",
        "numero": numero,
        "codigo_verificacao": "ABC123",
        "data_emissao": "2024-01-15T10:30:00-0300",
        "chave_nfse": chave,
    }


class TestL10nBrNfseNacional(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.company.write(
            {
                "provedor_nfse": "nfse_nacional",
                "nfse_environment": "2",
                "nfse_ssl_verify": False,
            }
        )
        cls.document_type = cls.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", MODELO_FISCAL_NFSE)], limit=1
        )
        cls.document_serie = cls.env["l10n_br_fiscal.document.serie"].search(
            [
                ("document_type_id", "=", cls.document_type.id),
                ("active", "=", True),
            ],
            limit=1,
        )
        if not cls.document_serie:
            cls.document_serie = cls.env["l10n_br_fiscal.document.serie"].create(
                {
                    "code": "001",
                    "name": "Série 1",
                    "document_type_id": cls.document_type.id,
                    "company_id": cls.company.id,
                    "active": True,
                }
            )
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "document_type_id": cls.document_type.id,
                "document_serie_id": cls.document_serie.id,
                "processador_edoc": PROCESSADOR_OCA,
                "nfse_environment": "2",
                "rps_number": "1234",
            }
        )

    def test_filter_true_for_nacional_provider(self):
        self.document.processador_edoc = PROCESSADOR_OCA
        self.assertTrue(filter_processador_nfse_nacional(self.document))

    def test_filter_false_for_other_provider(self):
        self.company.provedor_nfse = "focusnfe"
        self.assertFalse(filter_processador_nfse_nacional(self.document))
        self.company.provedor_nfse = "nfse_nacional"

    def test_filter_false_without_processador(self):
        self.document.processador_edoc = False
        self.assertFalse(filter_processador_nfse_nacional(self.document))
        self.document.processador_edoc = PROCESSADOR_OCA

    @patch(_PATCH_API)
    def test_fetch_danfse_returns_pdf_bytes(self, mock_api):
        """_fetch_danfse_from_service returns bytes when DANFSE service returns PDF."""
        fake_pdf = b"%PDF-1.4 content %%EOF"
        mock_api.return_value = _mock_response(200, content=fake_pdf)
        result = self.document._fetch_danfse_from_service("A" * 44)
        self.assertEqual(result, fake_pdf)
        self.assertEqual(mock_api.call_args[0][0], DANFSE_URL["2"])

    @patch(_PATCH_API)
    def test_fetch_danfse_returns_none_on_404(self, mock_api):
        mock_api.return_value = _mock_response(404)
        self.assertIsNone(self.document._fetch_danfse_from_service("A" * 44))

    @patch(_PATCH_API)
    def test_fetch_danfse_returns_none_on_invalid_content(self, mock_api):
        mock_api.return_value = _mock_response(200, content=b"not a pdf")
        self.assertIsNone(self.document._fetch_danfse_from_service("A" * 44))

    @patch(_PATCH_API)
    def test_fetch_xml_from_adn_returns_xml(self, mock_api):
        """_fetch_xml_from_adn returns decoded XML from the ADN service."""
        xml = b"<NFSe><Numero>1</Numero></NFSe>"
        mock_api.return_value = _mock_response(200, content=xml)
        result = self.document._fetch_xml_from_adn("A" * 44)
        self.assertIn("<NFSe>", result)
        self.assertEqual(mock_api.call_args[0][0], ADN_URL["2"])

    @patch(_PATCH_API)
    def test_fetch_xml_from_adn_returns_empty_on_error(self, mock_api):
        mock_api.return_value = _mock_response(404)
        self.assertEqual(self.document._fetch_xml_from_adn("A" * 44), "")

    @patch(_PATCH_PAYLOAD)
    @patch(_PATCH_API)
    def test_send_201_transitions_to_authorized(self, mock_api, mock_payload):
        """HTTP 201 from SEFIN emission → document transitions to AUTORIZADA."""
        chave = "A" * 44
        mock_payload.return_value = {}
        mock_api.side_effect = [
            _mock_response(201, _authorized_json(chave=chave)),
            _mock_response(200, content=b""),
            _mock_response(200, content=b"%PDF-1.4 %%EOF"),
        ]
        self.document.state_edoc = SITUACAO_EDOC_ENVIADA
        self.document._process_send_nacional(self.document)
        self.assertEqual(self.document.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(self.document.document_number, "999")
        self.assertEqual(self.document.nfse_nacional_chave, chave)

    @patch(_PATCH_PAYLOAD)
    @patch(_PATCH_API)
    def test_send_202_transitions_to_enviada(self, mock_api, mock_payload):
        """HTTP 202 from SEFIN emission → document transitions to ENVIADA."""
        mock_payload.return_value = {}
        mock_api.return_value = _mock_response(
            202, {"status": "processando_autorizacao"}
        )
        self.document._process_send_nacional(self.document)
        self.assertEqual(self.document.state_edoc, SITUACAO_EDOC_ENVIADA)

    @patch(_PATCH_PAYLOAD)
    @patch(_PATCH_API)
    def test_send_500_transitions_to_rejected(self, mock_api, mock_payload):
        """HTTP 500 from SEFIN emission → document transitions to REJEITADA."""
        mock_payload.return_value = {}
        mock_api.return_value = _mock_response(
            500, {"mensagem": "Internal server error"}
        )
        self.document._process_send_nacional(self.document)
        self.assertEqual(self.document.state_edoc, SITUACAO_EDOC_REJEITADA)

    @patch(_PATCH_API)
    def test_status_autorizado_transitions_to_authorized(self, mock_api):
        """Status query returning 'autorizado' → document transitions to AUTORIZADA."""
        chave = "B" * 44
        mock_api.side_effect = [
            _mock_response(200, _authorized_json(chave=chave, numero="888")),
            _mock_response(200, content=b""),
            _mock_response(200, content=b"%PDF-1.4 %%EOF"),
        ]
        self.document.state_edoc = SITUACAO_EDOC_ENVIADA
        self.document._process_status_nacional(self.document)
        self.assertEqual(self.document.state_edoc, SITUACAO_EDOC_AUTORIZADA)

    @patch(_PATCH_API)
    def test_status_erro_transitions_to_rejected(self, mock_api):
        """Status query returning 'erro' → document transitions to REJEITADA."""
        mock_api.return_value = _mock_response(
            200, {"status": "erro", "erros": [{"mensagem": "Invalid data"}]}
        )
        self.document.state_edoc = SITUACAO_EDOC_ENVIADA
        self.document._process_status_nacional(self.document)
        self.assertEqual(self.document.state_edoc, SITUACAO_EDOC_REJEITADA)

    @patch(_PATCH_API)
    def test_status_unavailable_returns_message(self, mock_api):
        """Non-200 status query → returns error message without raising."""
        mock_api.return_value = _mock_response(503, {})
        result = self.document._process_status_nacional(self.document)
        self.assertIn("Unable", result)

    @patch(_PATCH_API)
    def test_cancel_already_cancelled_skips_delete(self, mock_api):
        """When SEFIN already shows the document as cancelled, no DELETE is sent."""
        mock_api.return_value = _mock_response(200, {"status": "cancelado"})
        self.document.nfse_nacional_chave = "C" * 44
        self.document._cancel_nfse_nacional(self.document)
        self.assertEqual(mock_api.call_count, 1)

    @patch(_PATCH_API)
    def test_cancel_sends_delete_and_creates_event(self, mock_api):
        """Successful DELETE → cancel event created on the document."""
        mock_api.side_effect = [
            _mock_response(200, {"status": "autorizado"}),
            _mock_response(200, {"status": "cancelado", "codigo": "nfe_cancelada"}),
        ]
        self.document.nfse_nacional_chave = "D" * 44
        self.document._cancel_nfse_nacional(self.document)
        self.assertIsNotNone(self.document.cancel_event_id)

    @patch(_PATCH_API)
    def test_cancel_raises_on_unexpected_error(self, mock_api):
        """Unexpected DELETE response → UserError raised."""
        mock_api.side_effect = [
            _mock_response(200, {"status": "autorizado"}),
            _mock_response(500, {"mensagem": "Server failure"}),
        ]
        self.document.nfse_nacional_chave = "E" * 44
        with self.assertRaises(UserError):
            self.document._cancel_nfse_nacional(self.document)

    def test_cron_does_not_raise(self):
        # Document starts in draft — cron finds no ENVIADA records and is a no-op.
        self.env["l10n_br_fiscal.document"]._cron_document_status_nfse_nacional()

    def test_import_wizard_invalid_xml_raises(self):
        wizard = self.env["l10n_br_nfse_nacional.import.wizard"].create(
            {
                "company_id": self.company.id,
                "xml_file": base64.b64encode(b"not valid xml"),
                "xml_filename": "test.xml",
            }
        )
        with self.assertRaises(UserError):
            wizard.action_import()

    def test_import_wizard_valid_xml_creates_document(self):
        sample_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<NFSe>
    <Numero>12345</Numero>
    <ChaveAcesso>12345678901234567890123456789012345678901234</ChaveAcesso>
    <DtHrEmit>2024-01-15T10:30:00-03:00</DtHrEmit>
    <CodVerif>ABCD1234</CodVerif>
    <CNPJ>12345678000195</CNPJ>
    <xNome>Test Service Provider LTDA</xNome>
    <vServ>1000.00</vServ>
    <vISS>50.00</vISS>
    <xDisc>IT consulting services</xDisc>
</NFSe>"""
        wizard = self.env["l10n_br_nfse_nacional.import.wizard"].create(
            {
                "company_id": self.company.id,
                "xml_file": base64.b64encode(sample_xml),
                "xml_filename": "nfse_nacional_test.xml",
            }
        )
        result = wizard.action_import()
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "l10n_br_fiscal.document")

    def test_import_wizard_idempotent_for_existing_document(self):
        """Importing the same XML twice returns the same document (no duplicate)."""
        sample_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<NFSe>
    <Numero>99999</Numero>
    <ChaveAcesso>99999999999999999999999999999999999999999999</ChaveAcesso>
    <CodVerif>ZZ99</CodVerif>
    <CNPJ>12345678000195</CNPJ>
    <xNome>Idempotency Test LTDA</xNome>
    <vServ>500.00</vServ>
</NFSe>"""
        encoded = base64.b64encode(sample_xml)
        r1 = (
            self.env["l10n_br_nfse_nacional.import.wizard"]
            .create({"company_id": self.company.id, "xml_file": encoded})
            .action_import()
        )
        r2 = (
            self.env["l10n_br_nfse_nacional.import.wizard"]
            .create({"company_id": self.company.id, "xml_file": encoded})
            .action_import()
        )
        self.assertEqual(r1["res_id"], r2["res_id"])
