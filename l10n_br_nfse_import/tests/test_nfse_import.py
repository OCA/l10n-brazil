# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import SavepointCase

_ABRASF_SOAP_RESPONSE = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ConsultarNfseServicoTomadoResposta xmlns="http://www.abrasf.org.br/nfse.xsd">
      <ListaNfse>
        <CompNfse>
          <Nfse>
            <InfNfse>
              <Numero>99001</Numero>
              <CodigoVerificacao>ABC123</CodigoVerificacao>
              <DataEmissao>2024-03-15T10:30:00</DataEmissao>
              <PrestadorServico>
                <IdentificacaoPrestador>
                  <CpfCnpj><Cnpj>59594315000157</Cnpj></CpfCnpj>
                </IdentificacaoPrestador>
                <RazaoSocial>Empresa Prestadora Ltda</RazaoSocial>
              </PrestadorServico>
              <Servico>
                <Valores>
                  <ValorServicos>1500.00</ValorServicos>
                </Valores>
                <Discriminacao>Consultoria em TI</Discriminacao>
              </Servico>
            </InfNfse>
          </Nfse>
        </CompNfse>
      </ListaNfse>
    </ConsultarNfseServicoTomadoResposta>
  </soap:Body>
</soap:Envelope>"""

# ABRASF error response
_ABRASF_ERROR_RESPONSE = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ConsultarNfseServicoTomadoResposta xmlns="http://www.abrasf.org.br/nfse.xsd">
      <ListaMensagemRetorno>
        <MensagemRetorno>
          <Codigo>E10</Codigo>
          <Mensagem>Nota Fiscal nao encontrada</Mensagem>
        </MensagemRetorno>
      </ListaMensagemRetorno>
    </ConsultarNfseServicoTomadoResposta>
  </soap:Body>
</soap:Envelope>"""


class TestNfsDfeExtract(SavepointCase):
    """Unit tests for the ABRASF XML extraction helpers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.DfeCls = cls.env["l10n_br_nfse.dfe"]

    def test_parse_abrasf_response_extracts_nfse(self):
        dfe = self.DfeCls.new({})
        result = dfe._parse_abrasf_response(_ABRASF_SOAP_RESPONSE)
        self.assertEqual(len(result), 1)
        data = result[0]
        self.assertEqual(data["nfse_number"], "99001")
        self.assertEqual(data["verify_code"], "ABC123")
        self.assertEqual(data["provider_cnpj"], "59594315000157")
        self.assertEqual(data["provider_name"], "Empresa Prestadora Ltda")
        self.assertAlmostEqual(data["service_value"], 1500.0, places=2)
        self.assertIn("Consultoria", data["service_description"])
        self.assertEqual(data["emission_date"], "2024-03-15 10:30:00")
        self.assertIsNotNone(data["xml_content"])

    def test_parse_abrasf_response_error_returns_empty(self):
        dfe = self.DfeCls.new({})
        result = dfe._parse_abrasf_response(_ABRASF_ERROR_RESPONSE)
        self.assertEqual(result, [])

    def test_extract_comp_nfse_fields(self):
        """_extract_comp_nfse should map all CompNfse sub-fields correctly."""
        from lxml import etree as _etree

        comp_xml = b"""
        <CompNfse>
          <Nfse>
            <InfNfse>
              <Numero>5001</Numero>
              <CodigoVerificacao>XYZ789</CodigoVerificacao>
              <DataEmissao>2024-04-10T08:00:00</DataEmissao>
              <PrestadorServico>
                <IdentificacaoPrestador>
                  <CpfCnpj><Cnpj>11222333000181</Cnpj></CpfCnpj>
                </IdentificacaoPrestador>
                <RazaoSocial>Focus Provider SA</RazaoSocial>
              </PrestadorServico>
              <Servico>
                <Valores>
                  <ValorServicos>2000.00</ValorServicos>
                </Valores>
                <Discriminacao>Desenvolvimento de Software</Discriminacao>
              </Servico>
            </InfNfse>
          </Nfse>
        </CompNfse>"""
        comp = _etree.fromstring(comp_xml)
        result = self.DfeCls._extract_comp_nfse(comp)
        self.assertEqual(result["nfse_number"], "5001")
        self.assertEqual(result["verify_code"], "XYZ789")
        self.assertEqual(result["provider_cnpj"], "11222333000181")
        self.assertEqual(result["provider_name"], "Focus Provider SA")
        self.assertAlmostEqual(result["service_value"], 2000.0, places=2)
        self.assertIn("Desenvolvimento", result["service_description"])
        self.assertEqual(result["emission_date"], "2024-04-10 08:00:00")


class TestNfseReceived(SavepointCase):
    """Tests for the l10n_br_nfse.received model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")

    def _make_received(self, **kwargs):
        vals = {
            "company_id": self.company.id,
            "nfse_number": "12345",
            "verify_code": "ABC",
            "provider_cnpj": "11222333000181",
            "provider_name": "Test Provider Ltda",
            "service_value": 1000.0,
            "service_description": "Test service",
        }
        vals.update(kwargs)
        return self.env["l10n_br_nfse.received"].create(vals)

    def test_initial_state_is_pending(self):
        rec = self._make_received()
        self.assertEqual(rec.state, "pending")

    def test_action_cancel_sets_state(self):
        rec = self._make_received()
        rec.action_cancel()
        self.assertEqual(rec.state, "cancelled")

    def test_reset_to_pending(self):
        rec = self._make_received()
        rec.action_cancel()
        rec.action_reset_to_pending()
        self.assertEqual(rec.state, "pending")

    def test_create_xml_attachment(self):
        rec = self._make_received()
        rec._create_xml_attachment(b"<CompNfse/>")
        self.assertTrue(rec.attachment_id)
        self.assertIn("NFSe-12345", rec.attachment_id.name)


class TestNfseImportWizard(SavepointCase):
    """Tests for the review wizard that creates fiscal documents."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        # Ensure there is at least one incoming approved fiscal operation
        cls.fiscal_op = cls.env["l10n_br_fiscal.operation"].search(
            [("fiscal_operation_type", "=", "in"), ("state", "=", "approved")],
            limit=1,
        )

    def _make_received(self, nfse_number="77001", **kwargs):
        vals = {
            "company_id": self.company.id,
            "nfse_number": nfse_number,
            "verify_code": "TEST01",
            "provider_cnpj": "59594315000157",
            "provider_name": "Provider Test Ltda",
            "service_value": 1500.0,
            "service_description": "IT services",
        }
        vals.update(kwargs)
        return self.env["l10n_br_nfse.received"].create(vals)

    def test_wizard_prefills_from_received(self):
        received = self._make_received()
        wizard = (
            self.env["l10n_br_nfse.import.wizard"]
            .with_context(default_received_id=received.id)
            .create({})
        )
        self.assertEqual(wizard.nfse_number, received.nfse_number)
        self.assertEqual(wizard.verify_code, received.verify_code)
        self.assertAlmostEqual(wizard.service_value, 1500.0, places=2)
        self.assertEqual(wizard.received_id, received)

    def test_action_import_creates_fiscal_document(self):
        received = self._make_received(nfse_number="77002")
        wizard = (
            self.env["l10n_br_nfse.import.wizard"]
            .with_context(default_received_id=received.id)
            .create({})
        )
        if self.fiscal_op:
            wizard.fiscal_operation_id = self.fiscal_op

        wizard.action_import_document()

        self.assertEqual(received.state, "done")
        self.assertTrue(received.document_id)
        edoc = received.document_id
        self.assertEqual(edoc.fiscal_operation_type, "in")
        self.assertEqual(edoc.issuer, "partner")
        self.assertTrue(edoc.imported_document)
        self.assertEqual(edoc.document_number, "77002")

    def test_no_duplicate_on_second_import(self):
        received1 = self._make_received(nfse_number="77003")
        received2 = self._make_received(
            nfse_number="77003", provider_cnpj="59594315000157"
        )

        wizard1 = (
            self.env["l10n_br_nfse.import.wizard"]
            .with_context(default_received_id=received1.id)
            .create({})
        )
        if self.fiscal_op:
            wizard1.fiscal_operation_id = self.fiscal_op
        wizard1.action_import_document()
        doc1 = received1.document_id

        # Wizard for received2 should detect the existing doc
        wizard2 = (
            self.env["l10n_br_nfse.import.wizard"]
            .with_context(default_received_id=received2.id)
            .create({})
        )
        self.assertEqual(wizard2.document_id, doc1)

    def test_wizard_marks_received_done_on_link(self):
        """When a duplicate exists, linking should still set state=done."""
        received1 = self._make_received(nfse_number="77004")
        wizard1 = (
            self.env["l10n_br_nfse.import.wizard"]
            .with_context(default_received_id=received1.id)
            .create({})
        )
        if self.fiscal_op:
            wizard1.fiscal_operation_id = self.fiscal_op
        wizard1.action_import_document()

        received2 = self._make_received(nfse_number="77004")
        wizard2 = (
            self.env["l10n_br_nfse.import.wizard"]
            .with_context(default_received_id=received2.id)
            .create({})
        )
        wizard2.action_import_document()
        self.assertEqual(received2.state, "done")


class TestNfseDfeCreateRecords(SavepointCase):
    """Tests for _create_received_records deduplication logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")

    def _make_dfe(self):
        return self.env["l10n_br_nfse.dfe"].create(
            {
                "name": "Test DFe",
                "company_id": self.company.id,
                "webservice_url": "http://localhost/nfse",
            }
        )

    def test_create_received_records_no_duplicate(self):
        dfe = self._make_dfe()
        data = [
            {
                "nfse_number": "88001",
                "verify_code": "X",
                "provider_cnpj": "11222333000181",
                "provider_name": "Provider A",
                "service_value": 100.0,
                "service_description": "Service A",
                "emission_date": False,
                "xml_content": None,
            }
        ]
        dfe._create_received_records(data)
        count = self.env["l10n_br_nfse.received"].search_count(
            [("company_id", "=", self.company.id), ("nfse_number", "=", "88001")]
        )
        self.assertEqual(count, 1)

    def test_create_received_records_skips_duplicate(self):
        dfe = self._make_dfe()
        data = [
            {
                "nfse_number": "88002",
                "verify_code": "Y",
                "provider_cnpj": "11222333000181",
                "provider_name": "Provider B",
                "service_value": 200.0,
                "service_description": "Service B",
                "emission_date": False,
                "xml_content": None,
            }
        ]
        dfe._create_received_records(data)
        dfe._create_received_records(data)  # second time should skip
        count = self.env["l10n_br_nfse.received"].search_count(
            [("company_id", "=", self.company.id), ("nfse_number", "=", "88002")]
        )
        self.assertEqual(count, 1)
