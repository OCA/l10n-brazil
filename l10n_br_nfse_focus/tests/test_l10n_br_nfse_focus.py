# Copyright 2023 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

from requests import HTTPError

from odoo.exceptions import UserError
from odoo.tests import common

# Importing constants for Brazilian fiscal documents
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFSE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_REJEITADA,
)
from odoo.addons.l10n_br_nfse.models.document import filter_processador_edoc_nfse

# Importing necessary models and functions for NFSe processing
from ... import l10n_br_nfse_focus
from ..models.document import API_ENDPOINT, NFSE_URL, Document, filter_focusnfe

# Mock path for testing purposes
MOCK_PATH = "odoo.addons.l10n_br_nfse_focus"

# Payload for testing NFSe (Nota Fiscal de Serviços Eletrônica) operations
PAYLOAD = []
PAYLOAD.append(
    {
        "rps": {
            "cnpj": "12345678901234",
            "inscricao_municipal": "12345",
            "id": "rps132",
            "numero": "132",
            "serie": "2",
            "tipo": "1",
            "data_emissao": "2024-02-20T17:01:47",
            "date_in_out": "2024-02-20T17:01:57",
            "natureza_operacao": "1",
            "regime_especial_tributacao": "1",
            "optante_simples_nacional": "1",
            "incentivador_cultural": "2",
            "status": "1",
            "rps_substitiuido": False,
            "intermediario_servico": False,
            "codigo_obra": "",
            "art": "",
            "carga_tributaria": 0.0,
            "total_recebido": 100.0,
            "carga_tributaria_estimada": 0.0,
        }
    },
)
PAYLOAD.append(
    {
        "service": {
            "valor_servicos": 100.0,
            "valor_deducoes": 0.0,
            "valor_pis": 0.65,
            "valor_pis_retido": 0.65,
            "valor_cofins": 3.0,
            "valor_cofins_retido": 3.0,
            "valor_inss": 0.0,
            "valor_inss_retido": 0.0,
            "valor_ir": 1.5,
            "valor_ir_retido": 1.5,
            "valor_csll": 1.0,
            "valor_csll_retido": 1.0,
            "iss_retido": "1",
            "valor_iss": 0.0,
            "valor_iss_retido": 4.0,
            "outras_retencoes": 0.0,
            "base_calculo": 100.0,
            "aliquota": 0.04,
            "valor_liquido_nfse": 89.85,
            "item_lista_servico": "1712",
            "codigo_tributacao_municipio": "171202211",
            "municipio_prestacao_servico": "",
            "discriminacao": "[ODOO_DEV] Customized Odoo Development",
            "codigo_cnae": False,
            "valor_desconto_incondicionado": 0.0,
            "codigo_municipio": "3505708",
        }
    }
)
PAYLOAD.append(
    {
        "recipient": {
            "cnpj": "07504505000132",
            "cpf": False,
            "email": "contato@focusnfe.com.br",
            "inscricao_municipal": False,
            "inscricao_estadual": False,
            "razao_social": "Acras Tecnologia da Informação LTDA",
            "endereco": "Rua Dias da Rocha Filho",
            "numero": "999",
            "bairro": "Alto da XV",
            "codigo_municipio": "4106902",
            "descricao_municipio": "São José dos Pinhais",
            "uf": "PR",
            "municipio": "Curitiba",
            "cep": "83050580",
            "complemento": "Prédio 04 - Sala 34C",
        }
    }
)

# Reference for testing payload
PAYLOAD_REF = "rps132"


class MockResponse:
    """Mock response class for simulating HTTP responses in tests."""

    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        """Returns JSON data."""
        return self._json_data

    @property
    def text(self):
        """Returns text representation of JSON data."""
        return str(self._json_data)

    def raise_for_status(self):
        """Raises HTTPError for status codes 400-599."""
        if 400 <= self.status_code < 600:
            raise HTTPError(f"{self.status_code} HTTP error")


class TestL10nBrNfseFocus(common.TransactionCase):
    """Test class for Brazilian NFSe Focus integration."""

    def setUp(self):
        """Sets up test environment."""
        super().setUp()
        self.tpAmb = "2"  # Environment type: 1 for production, 2 for test
        self.token = "123456789"  # Example token for authentication
        self.company = self.env.ref("base.main_company")  # Reference to main company
        self.company.focusnfe_homologation_token = self.token  # Setting company token
        self.company.provedor_nfse = "focusnfe"  # Setting NFSe provider to focusnfe
        self.nfse_demo = self.env.ref(
            "l10n_br_fiscal.demo_nfse_same_state"
        )  # NFSe demo document
        self.nfse_demo.document_number = "0001"  # Setting document number
        self.nfse_demo.rps_number = "0002"  # Setting RPS number
        self.nfse_focus = self.env["focusnfe.nfse"]  # NFSe processing model

    def test_filter_processador_edoc_nfse(self):
        """Tests filtering of NFSe documents for OCA processor."""
        record = self.nfse_demo
        record.processador_edoc = PROCESSADOR_OCA  # Setting document processor to OCA
        record.document_type_id.code = (
            MODELO_FISCAL_NFSE  # Setting document type to NFSe
        )

        result = filter_processador_edoc_nfse(record)  # Applying filter

        self.assertEqual(
            record.processador_edoc, PROCESSADOR_OCA
        )  # Asserting processor is OCA
        self.assertIn(
            record.document_type_id.code, MODELO_FISCAL_NFSE
        )  # Asserting document type is NFSe
        self.assertEqual(result, True)  # Asserting filter result is True

        record.processador_edoc = None  # Resetting document processor
        # Setting document type to NFe
        record.document_type_id.code = MODELO_FISCAL_NFE

        result = filter_processador_edoc_nfse(record)  # Applying filter again

        self.assertNotEqual(
            record.processador_edoc, PROCESSADOR_OCA
        )  # Asserting processor is not OCA
        self.assertNotIn(
            record.document_type_id.code, MODELO_FISCAL_NFSE
        )  # Asserting document type is not NFSe
        self.assertEqual(result, False)  # Asserting filter result is False

    def test_filter_focusnfe(self):
        """Tests setting of NFSe provider to focusnfe for a document."""
        record = self.nfse_demo
        filter_focusnfe(record)  # Applying filter

        self.assertEqual(
            record.company_id.provedor_nfse, "focusnfe"
        )  # Asserting provider is set to focusnfe

    @patch("odoo.addons.l10n_br_nfse_focus.models.document.requests.request")
    def test_processar_documento(self, mock_post):
        """Tests document processing with mocked POST request."""
        mock_post.return_value.status_code = 200  # Simulating successful POST request
        mock_post.return_value.json.return_value = {
            "status": "simulado"
        }  # Mocking JSON response

        result = self.nfse_focus.process_focus_nfse_document(
            PAYLOAD, PAYLOAD_REF, self.company, self.tpAmb
        )  # Processing document

        self.assertEqual(result.status_code, 200)  # Asserting successful status code
        self.assertEqual(
            result.json(), {"status": "simulado"}
        )  # Asserting expected JSON response

    @patch("odoo.addons.l10n_br_nfse_focus.models.document.requests.request")
    def test_make_focus_nfse_http_request_generic(self, mock_request):
        """
        Tests generic HTTP request for Focus NFSe operations with mocked responses.
        """
        # Configuring mock to simulate different HTTP responses based on the method
        mock_request.side_effect = (
            lambda method, url, data, params, auth: mock_response_based_on_method(
                method, data
            )
        )

        # Auxiliary function to simulate responses based on the HTTP method
        def mock_response_based_on_method(method, data):
            if method == "POST":
                return MockResponse(
                    200, {"status": "success"}
                )  # Mocking success for POST
            elif method == "GET":
                return MockResponse(
                    200, {"status": "success", "data": {"nfse_info": "…"}}
                )  # Mocking success with data for GET
            elif method == "DELETE":
                return MockResponse(
                    204, {"status": "success"}
                )  # Mocking success for DELETE
            else:
                return MockResponse(
                    500, "Internal server error"
                )  # Mocking server error for other methods

        # Testing POST method
        URL = (
            NFSE_URL[self.tpAmb] + API_ENDPOINT["envio"]
        )  # Constructing URL for sending NFSe
        result_post = self.nfse_focus._make_focus_nfse_http_request(
            "POST", URL, self.token, PAYLOAD, PAYLOAD_REF
        )  # Making POST request
        self.assertEqual(result_post.status_code, 200)  # Asserting status code 200
        self.assertEqual(
            result_post.json(), {"status": "success"}
        )  # Asserting JSON response

        # Testing GET method
        URL = (
            NFSE_URL[self.tpAmb] + API_ENDPOINT["status"]
        )  # Constructing URL for checking status
        result_get = self.nfse_focus._make_focus_nfse_http_request(
            "GET", URL, self.token, PAYLOAD, PAYLOAD_REF
        )  # Making GET request
        self.assertEqual(result_get.status_code, 200)  # Asserting status code 200
        self.assertEqual(
            result_get.json(), {"status": "success", "data": {"nfse_info": "…"}}
        )  # Asserting JSON response with data

        # Testing DELETE method
        URL = (
            NFSE_URL[self.tpAmb] + API_ENDPOINT["cancelamento"]
        )  # Constructing URL for cancellation
        result_delete = self.nfse_focus._make_focus_nfse_http_request(
            "DELETE", URL, self.token, PAYLOAD, PAYLOAD_REF
        )  # Making DELETE request
        self.assertEqual(result_delete.status_code, 204)  # Asserting status code 204
        self.assertEqual(
            result_delete.json(), {"status": "success"}
        )  # Asserting JSON response

    @patch("odoo.addons.l10n_br_nfse_focus.models.document.requests.request")
    def test_consulta_nfse_rps(self, mock_get):
        """Tests NFSe query by RPS with mocked GET request."""
        mock_get.return_value.status_code = 200  # Simulating successful GET request
        mock_get.return_value.json.return_value = {
            "status": "success",
            "data": {"nfse_info": "…"},
        }  # Mocking JSON response

        result = self.nfse_focus.query_focus_nfse_by_rps(
            PAYLOAD_REF, 0, self.company, self.tpAmb
        )  # Querying NFSe by RPS

        self.assertEqual(result.status_code, 200)  # Asserting successful status code
        self.assertEqual(
            result.json(), {"status": "success", "data": {"nfse_info": "…"}}
        )  # Asserting expected JSON response

    @patch("odoo.addons.l10n_br_nfse_focus.models.document.requests.request")
    def test_cancela_documento(self, mock_delete):
        """Tests document cancellation with mocked DELETE request."""
        mock_delete.return_value.status_code = (
            204  # Simulating successful DELETE request
        )
        result = self.nfse_focus.cancel_focus_nfse_document(
            PAYLOAD_REF, "Teste de cancelamento", self.company, self.tpAmb
        )  # Cancelling document

        self.assertEqual(result.status_code, 204)  # Asserting status code 204

    def test_make_focus_nfse_pdf(self):
        """Tests generation of NFSe PDF."""
        record = self.nfse_demo
        record.processador_edoc = PROCESSADOR_OCA  # Setting document processor to OCA
        record.document_type_id.code = (
            MODELO_FISCAL_NFSE  # Setting document type to NFSe
        )

        # Reading PDF example for testing
        pdf_path = os.path.join(
            l10n_br_nfse_focus.__path__[0], "tests", "nfse", "pdf_example.pdf"
        )

        with open(pdf_path, "rb") as file:
            content = file.read()  # Reading PDF content

        record.make_focus_nfse_pdf(content)  # Generating NFSe PDF

        self.assertTrue(record.document_number)  # Asserting document number is set
        self.assertEqual(
            record.file_report_id.name, "NFS-e-" + record.document_number + ".pdf"
        )  # Asserting file name
        self.assertEqual(
            record.file_report_id.res_model, record._name
        )  # Asserting model name
        # Asserting record ID
        self.assertEqual(record.file_report_id.res_id, record.id)
        self.assertEqual(
            record.file_report_id.mimetype, "application/pdf"
        )  # Asserting MIME type
        self.assertEqual(record.file_report_id.type, "binary")  # Asserting file type

        # Testing with no document number
        record.document_number = None
        record.make_focus_nfse_pdf(content)  # Generating NFSe PDF again

        self.assertFalse(record.document_number)  # Asserting no document number
        self.assertEqual(
            record.file_report_id.name, "RPS-" + record.rps_number + ".pdf"
        )  # Asserting file name for RPS

        # Testing with non-filtered conditions
        record.processador_edoc = ""
        # Setting document type to NFe
        record.document_type_id.code = MODELO_FISCAL_NFE

        with open(pdf_path, "rb") as file:
            content = file.read()  # Reading PDF content again

        with patch(
            "odoo.addons.l10n_br_nfse.models.document.Document.make_pdf"
        ) as mock_super_make_pdf:
            record.make_focus_nfse_pdf(content)  # Attempting to generate PDF

        # Asserting superclass method called once
        mock_super_make_pdf.assert_called_once()

    def test_serialize(self):
        """Tests serialization of document data."""
        doc = self.nfse_demo
        edocs = []
        with patch.object(Document, "_serialize", return_value=edocs) as mock_serialize:
            result = doc._serialize(edocs)  # Serializing document data

        mock_serialize.assert_called_once_with(edocs)  # Asserting method called once
        self.assertEqual(result, edocs)  # Asserting serialization result

    def test_document_export(self):
        """Tests export of document data."""
        record = self.nfse_demo
        record.processador_edoc = PROCESSADOR_OCA  # Setting document processor to OCA
        record.document_type_id.code = MODELO_FISCAL_NFE  # Setting document type to NFe

        # Testing with non-filtered conditions
        record = self.nfse_demo
        record.company_id.provedor_nfse = None  # Resetting NFSe provider

        record._document_export()  # Exporting document data

        self.assertFalse(
            record.company_id.provedor_nfse
        )  # Asserting NFSe provider not set

        # Testing with filtered conditions
        record = self.nfse_demo
        record.company_id.provedor_nfse = (
            "focusnfe"  # Setting NFSe provider to focusnfe
        )
        record.processador_edoc = PROCESSADOR_OCA  # Setting processor to OCA
        record.document_type_id.code = (
            MODELO_FISCAL_NFSE  # Setting document type to NFSe
        )

        record._document_export()  # Exporting document data again

        self.assertTrue(
            record.company_id.provedor_nfse
        )  # Asserting NFSe provider is set
        self.assertTrue(
            record.authorization_event_id
        )  # Asserting authorization event is set

    @patch(
        "odoo.addons.l10n_br_nfse_focus.models.document.FocusnfeNfse.query_focus_nfse_by_rps"
    )
    def test_document_status(self, mock_query):
        """Tests querying document status."""
        document = self.nfse_demo
        document.processador_edoc = PROCESSADOR_OCA  # Setting processor to OCA
        document.document_type_id.code = (
            MODELO_FISCAL_NFSE  # Setting document type to NFSe
        )
        document.document_date = datetime.strptime(
            "2024-01-01T05:10:12", "%Y-%m-%dT%H:%M:%S"
        )  # Setting document date
        document.date_in_out = datetime.strptime(
            "2024-01-01T05:10:12", "%Y-%m-%dT%H:%M:%S"
        )  # Setting date in/out

        # Simulating response: Unable to retrieve the document status.
        result = document._document_status()  # Querying document status

        self.assertEqual(
            result, "Unable to retrieve the document status."
        )  # Asserting result message

    @patch(
        "odoo.addons.l10n_br_nfse_focus.models.document.FocusnfeNfse._make_focus_nfse_http_request"  # noqa: E501
    )
    def test_cancel_document_focus_with_error(self, mock_request):
        """Tests document cancellation with simulated error."""
        # Configuring mock to raise a UserError in response to a simulated
        # HTTP 400 error
        mock_request.side_effect = UserError(
            "Error communicating with NFSe service: 400 Bad Request"
        )

        document = self.nfse_demo
        document.processador_edoc = PROCESSADOR_OCA  # Setting processor to OCA
        document.document_type_id.code = (
            MODELO_FISCAL_NFSE  # Setting document type to NFSe
        )
        document.document_date = datetime.strptime(
            "2024-01-01T05:10:12", "%Y-%m-%dT%H:%M:%S"
        )  # Setting document date
        document.date_in_out = datetime.strptime(
            "2024-01-01T05:10:12", "%Y-%m-%dT%H:%M:%S"
        )  # Setting date in/out

        with self.assertRaises(UserError) as context:
            document.cancel_document_focus()  # Attempting to cancel document

        # Checking if the expected error message is in the raised exception
        self.assertIn(
            "Error communicating with NFSe service: 400 Bad Request",
            str(context.exception),
        )

    @patch(
        "odoo.addons.l10n_br_nfse_focus.models.document.FocusnfeNfse.process_focus_nfse_document"  # noqa: E501
    )
    def test_eletronic_document_send(self, mock_process_focus_nfse_document):
        """Tests sending of electronic document with simulated responses."""
        # Configuring mock to simulate different responses
        # Mocking response for status 202
        mock_response_202 = MagicMock()
        mock_response_202.status_code = 202
        mock_response_202.json.return_value = {"status": "processando_autorizacao"}

        # Mocking response for status 422
        mock_response_422 = MagicMock()
        mock_response_422.status_code = 422
        mock_response_422.json.return_value = {"codigo": "algum_codigo_erro"}

        # Mocking response for status 500
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_response_500.json.return_value = {"erro": "erro interno"}

        # Simulating sequentially responses for subsequent calls
        mock_process_focus_nfse_document.side_effect = [
            mock_response_202,
            mock_response_422,
            mock_response_500,
        ]

        document = self.nfse_demo
        document.processador_edoc = PROCESSADOR_OCA  # Setting processor to OCA
        document.document_type_id.code = (
            MODELO_FISCAL_NFSE  # Setting document type to NFSe
        )
        document.document_date = datetime.strptime(
            "2024-01-01T05:10:12", "%Y-%m-%dT%H:%M:%S"
        )  # Setting document date
        document.date_in_out = datetime.strptime(
            "2024-01-01T05:10:12", "%Y-%m-%dT%H:%M:%S"
        )  # Setting date in/out

        # Testing logic for response 202
        document._eletronic_document_send()  # Sending electronic document
        # Here you would verify if the document state was correctly updated
        # This depends on how you implemented the state update logic in your method

        self.assertEqual(
            document.state,
            SITUACAO_EDOC_ENVIADA,
            "The document state should be updated to sent due to error 422",
        )

        # Testing logic for response 422
        document._eletronic_document_send()  # Sending electronic document again
        self.assertEqual(
            document.state,
            SITUACAO_EDOC_REJEITADA,
            "The document state should be 'rejected' after processing with status 422",
        )

        # Testing sending of the document with response 500
        document._eletronic_document_send()  # Sending electronic document once more
        self.assertEqual(
            document.state,
            SITUACAO_EDOC_REJEITADA,
            "The document state should remain 'rejected' "
            "after processing with status 500",
        )

        # Checking if the processing method was called three times,
        # once for each test scenario
        self.assertEqual(
            mock_process_focus_nfse_document.call_count,
            3,
            "The processing method should be called three times",
        )

    def test_cron_document_status_focus(self):
        """Tests scheduled job for updating document status."""
        record = self.nfse_demo
        record.state = "enviada"  # Setting document state to 'sent'

        with patch(
            "odoo.addons.l10n_br_nfse_focus.models.document.Document.search"
        ) as mock_search:
            with patch(
                "odoo.addons.l10n_br_nfse_focus.models.document.Document.filtered"
            ) as mock_filtered:
                with patch(
                    "odoo.addons.l10n_br_nfse_focus.models.document."
                    "Document._document_status"
                ) as mock_document_status:
                    mock_search.return_value = record  # Mocking search return
                    mock_filtered.return_value = record  # Mocking filtered return

                    record._cron_document_status_focus()  # Executing scheduled job

                    self.assertTrue(mock_search)  # Asserting search was executed
                    mock_search.assert_called_once_with(
                        [("state", "in", ["enviada"])], limit=25
                    )  # Asserting search criteria
                    # Asserting document status check
                    mock_document_status.assert_called_once()

    @patch(
        "odoo.addons.l10n_br_nfse_focus.models.document.Document.cancel_document_focus"
    )
    def test_exec_before_SITUACAO_EDOC_CANCELADA(self, mock_cancel_document_focus):
        """Tests execution before setting document status to cancelled."""
        record = self.nfse_demo
        mock_cancel_document_focus.return_value = (
            True  # Simulating successful cancellation
        )
        result = record._exec_before_SITUACAO_EDOC_CANCELADA(
            SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_A_ENVIAR
        )  # Executing before status change
        # Asserting cancellation was attempted
        mock_cancel_document_focus.assert_called_once()
        self.assertEqual(
            result, mock_cancel_document_focus.return_value
        )  # Asserting expected result
