# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import gzip
from datetime import timedelta
from io import BytesIO
from unittest import mock

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from odoo.addons.l10n_br_fiscal_dfe.constants.dfe import DFE_INTERVAL_NO_DOCS
from odoo.addons.l10n_br_nfse_dfe.services.adn_dfe import AdnDfeClient, AdnDfeResponse

PROVIDER_CNPJ = "59594315000157"
DECOY_CNPJ = "81493979000189"
TAKER_CNPJ = "81583054000129"
ACCESS_KEY = "8" * 50
NS = "http://www.sped.fazenda.gov.br/nfse"


def nfse_xml(
    access_key=ACCESS_KEY,
    retention="1",
    serie="00007",
    provider_cnpj=PROVIDER_CNPJ,
    provider_name="Provider Test",
    prest_extra="",
):
    """National NFS-e with a decoy CNPJ before the provider."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<NFSe xmlns="{NS}">
  <infNFSe Id="NFS{access_key}">
    <nNFSe>123</nNFSe>
    <dhProc>2023-09-09T12:42:06-03:00</dhProc>
    <cLocIncid>3550308</cLocIncid>
    <emit>
      <CNPJ>{DECOY_CNPJ}</CNPJ>
      <xNome>Decoy Emitter</xNome>
    </emit>
    <valores>
      <vBC>20.00</vBC>
      <pAliqAplic>2.00</pAliqAplic>
      <vISSQN>0.40</vISSQN>
      <vLiq>20.00</vLiq>
    </valores>
    <DPS>
      <infDPS>
        <dhEmi>2023-09-09T09:42:06-03:00</dhEmi>
        <serie>{serie}</serie>
        <nDPS>2</nDPS>
        <prest>
          <CNPJ>{provider_cnpj}</CNPJ>
          <xNome>{provider_name}</xNome>
          {prest_extra}
        </prest>
        <toma>
          <CNPJ>{TAKER_CNPJ}</CNPJ>
          <xNome>Empresa Lucro Presumido</xNome>
        </toma>
        <serv>
          <cServ>
            <cTribNac>010101</cTribNac>
            <cNBS>123456789</cNBS>
            <xDescServ>Consulting</xDescServ>
          </cServ>
        </serv>
        <valores>
          <vServPrest><vServ>20.00</vServ></vServPrest>
          <trib><tribMun><tpRetISSQN>{retention}</tpRetISSQN></tribMun></trib>
        </valores>
      </infDPS>
    </DPS>
  </infNFSe>
</NFSe>
""".encode()


def event_xml(access_key=ACCESS_KEY, event_code="101101"):
    """National event: the code is the ``eNNNNNN`` child, not ``tpEvento``."""
    ident = f"PRE{access_key}{event_code}001"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<evento xmlns="{NS}" versao="1.00">
  <infEvento>
    <pedRegEvento versao="1.00">
      <infPedReg Id="{ident}">
        <chNFSe>{access_key}</chNFSe>
        <e{event_code}>
          <xDesc>Cancellation</xDesc>
        </e{event_code}>
      </infPedReg>
    </pedRegEvento>
  </infEvento>
</evento>
""".encode()


def gzip_base64(payload):
    buffer = BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb") as handle:
        handle.write(payload)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def response(status, body=None, headers=None):
    return AdnDfeResponse(
        status_code=status,
        body=body,
        content=b"",
        headers=headers or {},
        text="",
    )


class TestNfseDfe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.company.nfse_dfe_environment = "producao_restrita"
        cls.provider = cls.env["res.partner"].search(
            [("cnpj_cpf_stripped", "=", PROVIDER_CNPJ)], limit=1
        )
        if not cls.provider:
            raise AssertionError("Demo provider CNPJ 59594315000157 was not found")

    def _documents(self):
        return self.env["l10n_br_fiscal_dfe.document"].search(
            [("company_id", "=", self.company.id), ("fiscal_type", "=", "nfse")]
        )

    def _logs(self):
        return self.env["l10n_br_fiscal_dfe.distribution_log"].search(
            [("company_id", "=", self.company.id), ("fiscal_type", "=", "nfse")]
        )

    def _distribute(self, side_effect, page_size=None):
        patchers = [
            mock.patch.object(type(self.company), "_nfse_adn_request", side_effect)
        ]
        if page_size:
            patchers.append(
                mock.patch(
                    "odoo.addons.l10n_br_nfse_dfe.models.res_company.NFSE_LOTE_SIZE",
                    page_size,
                )
            )
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.company._nfse_document_distribution()

    def test_lote_note_event_and_dedup(self):
        note = {
            "NSU": 10,
            "ChaveAcesso": ACCESS_KEY,
            "TipoDocumento": "NFSE",
            "ArquivoXml": gzip_base64(nfse_xml()),
        }
        event = {
            "NSU": 11,
            "ChaveAcesso": ACCESS_KEY,
            "TipoDocumento": "EVENTO",
            "TipoEvento": "CANCELAMENTO",
            "ArquivoXml": base64.b64encode(event_xml()).decode("ascii"),
        }
        calls = []

        def side_effect(_company, path, params=None):
            calls.append((path, params))
            return response(200, {"LoteDFe": [note, event]})

        self._distribute(side_effect)
        documents = self._documents()
        if not documents:
            self.fail(self._logs().mapped("message"))
        self.assertEqual(len(documents), 1)
        document = documents
        self.assertEqual(document.access_key, ACCESS_KEY)
        self.assertEqual(document.emitter, "Provider Test")
        self.assertEqual(document.document_number, "123")
        self.assertEqual(document.serie, "7")
        self.assertEqual(document.document_amount, 20.0)
        self.assertEqual(document.document_state, "3")
        self.assertEqual(document.document_state_label, "Cancelled")
        self.assertEqual(document.partner_id, self.provider)
        self.assertFalse(document.is_own_document)
        self.assertEqual(document.document_emission_date.hour, 12)
        self.assertEqual(
            set(document.dfe_ids.mapped("document_type_dfe")), {"complete", "event"}
        )
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0][0].endswith("/contribuintes/DFe/0"))
        self.assertEqual(calls[0][1]["cnpjConsulta"], TAKER_CNPJ)

        self.company.nfse_dfe_next_query = False
        self.company._nfse_document_distribution()
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(self._documents()), 1)
        self.assertEqual(len(document.dfe_ids), 2)

    def test_pagination_stops_on_404(self):
        calls = []

        def side_effect(_company, path, params=None):
            calls.append(path)
            if len(calls) == 1:
                return response(
                    200,
                    {
                        "LoteDFe": [
                            {
                                "NSU": 10,
                                "ChaveAcesso": ACCESS_KEY,
                                "TipoDocumento": "NFSE",
                                "ArquivoXml": base64.b64encode(nfse_xml()).decode(),
                            }
                        ]
                    },
                )
            return response(404)

        self.company.nfse_last_nsu = "0"
        self._distribute(side_effect, page_size=1)
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[1].endswith("/contribuintes/DFe/10"))
        self.assertEqual(self.company.nfse_last_nsu, "000000000000010")
        self.assertEqual(self.company.nfse_dfe_last_status_code, "137")

    def test_404_keeps_cursor_and_schedules_empty_interval(self):
        self.company.nfse_last_nsu = "000000000000005"
        self.company.nfse_dfe_next_query = False
        before = fields.Datetime.now()

        def side_effect(_company, path, params=None):
            return response(404)

        self._distribute(side_effect)
        self.assertEqual(self.company.nfse_last_nsu, "000000000000005")
        self.assertEqual(self.company.nfse_dfe_last_status_code, "137")
        delta = self.company.nfse_dfe_next_query - before
        self.assertGreaterEqual(delta, DFE_INTERVAL_NO_DOCS - timedelta(seconds=5))
        self.assertLessEqual(delta, DFE_INTERVAL_NO_DOCS + timedelta(minutes=2))

    def test_429_honors_retry_after(self):
        self.company.nfse_last_nsu = "000000000000005"
        self.company.nfse_dfe_next_query = False
        before = fields.Datetime.now()

        def side_effect(_company, path, params=None):
            return response(429, headers={"Retry-After": "90"})

        self._distribute(side_effect)
        self.assertEqual(self.company.nfse_last_nsu, "000000000000005")
        self.assertEqual(self.company.nfse_dfe_last_status_code, "656")
        seconds = (self.company.nfse_dfe_next_query - before).total_seconds()
        self.assertGreaterEqual(seconds, 85)
        self.assertLessEqual(seconds, 100)

    def test_nfe_distribution_does_not_call_adn(self):
        parent = (
            "odoo.addons.l10n_br_fiscal_dfe.models.res_company."
            "ResCompany._dfe_document_distribution"
        )
        with (
            mock.patch.object(
                type(self.company), "_nfse_document_distribution"
            ) as nfse_loop,
            mock.patch(parent, return_value=None) as soap_loop,
        ):
            self.company._dfe_document_distribution("nfe")
        nfse_loop.assert_not_called()
        soap_loop.assert_called_once()

    def test_nfse_distribution_dispatches_to_adn_loop(self):
        with mock.patch.object(
            type(self.company), "_nfse_document_distribution", return_value=None
        ) as nfse_loop:
            self.company._dfe_document_distribution("nfse")
        nfse_loop.assert_called_once()

    def test_44_digit_key_still_matches_partner(self):
        digits = "31282204000196"
        partner = self.env["res.partner"].search(
            [("cnpj_cpf_stripped", "=", digits)], limit=1
        )
        if not partner:
            partner = self.env["res.partner"].create(
                {
                    "name": "NF-e Partner",
                    "is_company": True,
                    "vat": "31.282.204/0001-96",
                }
            )
        key = f"352001{digits}550010000000012062777161"
        self.assertEqual(len(key), 44)
        document = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": key,
                "company_id": self.company.id,
                "fiscal_type": "nfe",
            }
        )
        self.assertEqual(len(document.access_key), 44)
        self.assertEqual(document.partner_id, partner)
        nfse_key = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "9" * 50,
                "company_id": self.company.id,
                "fiscal_type": "nfse",
                "vat": self.company.vat,
            }
        )
        self.assertEqual(len(nfse_key.access_key), 50)
        self.assertTrue(nfse_key.is_own_document)

    def test_import_requires_complete_xml(self):
        document = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "6" * 50,
                "company_id": self.company.id,
                "fiscal_type": "nfse",
            }
        )
        with self.assertRaises(UserError):
            document.import_document()

    def test_specific_search_accepts_50_digits(self):
        wizard = self.env["dfe.specific.search.wizard"].create(
            {
                "company_id": self.company.id,
                "fiscal_type": "nfse",
                "search_type": "access_key",
            }
        )
        with self.assertRaises(UserError):
            wizard._validate_access_key("1" * 44)
        wizard._validate_access_key(ACCESS_KEY)

    def test_adn_client_keeps_tls_verification(self):
        client = AdnDfeClient(
            "https://adn.producaorestrita.nfse.gov.br", "/tmp/unused.pem"
        )
        self.assertIs(client._session.verify, True)
        mocked = mock.Mock(
            status_code=200,
            content=b"",
            headers={},
            text="",
        )
        mocked.json.return_value = {}
        with mock.patch.object(client._session, "get", return_value=mocked) as get:
            client.get("/contribuintes/DFe/0", params={"lote": "true"})
        self.assertTrue(get.call_args.args[0].endswith("/contribuintes/DFe/0"))

    def test_event_before_note_stays_cancelled(self):
        key = "3" * 50
        event = {
            "NSU": 2,
            "ChaveAcesso": key,
            "TipoDocumento": "EVENTO",
            "TipoEvento": "CANCELAMENTO",
            "ArquivoXml": base64.b64encode(event_xml(access_key=key)).decode(),
        }
        note = {
            "NSU": 1,
            "ChaveAcesso": key,
            "TipoDocumento": "NFSE",
            "ArquivoXml": gzip_base64(nfse_xml(access_key=key)),
        }
        self.company._nfse_process_item(event)
        self.company._nfse_process_item(note)
        document = self._documents().filtered(lambda rec: rec.access_key == key)
        self.assertEqual(document.document_state, "3")

    def test_registration_request_does_not_cancel(self):
        key = "4" * 50
        note = {
            "NSU": 3,
            "ChaveAcesso": key,
            "TipoDocumento": "NFSE",
            "ArquivoXml": gzip_base64(nfse_xml(access_key=key)),
        }
        request = {
            "NSU": 4,
            "ChaveAcesso": key,
            "TipoDocumento": "PEDIDO_REGISTRO_EVENTO",
            "TipoEvento": "CANCELAMENTO",
            "ArquivoXml": base64.b64encode(event_xml(access_key=key)).decode(),
        }
        self.company._nfse_process_items([note, request])
        document = self._documents().filtered(lambda rec: rec.access_key == key)
        self.assertEqual(document.document_state, "1")

    def test_dps_item_is_skipped(self):
        key = "5" * 50
        item = {
            "NSU": 21,
            "ChaveAcesso": key,
            "TipoDocumento": "DPS",
            "ArquivoXml": gzip_base64(nfse_xml(access_key=key)),
        }
        self.company._nfse_process_items([item])
        self.assertFalse(self._documents().filtered(lambda rec: rec.access_key == key))

    def test_bad_item_does_not_freeze_the_nsu(self):
        bad = {
            "NSU": 11,
            "ChaveAcesso": "6" * 50,
            "TipoDocumento": "NFSE",
            "ArquivoXml": gzip_base64(nfse_xml(access_key="6" * 50)),
        }
        good = {
            "NSU": 12,
            "ChaveAcesso": "7" * 50,
            "TipoDocumento": "NFSE",
            "ArquivoXml": gzip_base64(nfse_xml(access_key="7" * 50)),
        }
        original = type(self.company)._nfse_create_note

        def explode(company, item, xml_bytes, nsu):
            if str(item.get("NSU")) == "11":
                raise RuntimeError("broken item")
            return original(company, item, xml_bytes, nsu)

        def side_effect(_company, path, params=None):
            return response(200, {"LoteDFe": [bad, good]})

        with (
            mock.patch.object(type(self.company), "_nfse_create_note", explode),
            mute_logger("odoo.addons.l10n_br_nfse_dfe.models.res_company"),
        ):
            self._distribute(side_effect)
        self.assertTrue(self.company.nfse_last_nsu.endswith("12"))
        stored = self._documents().mapped("access_key")
        self.assertIn("7" * 50, stored)
        self.assertNotIn("6" * 50, stored)

    def test_series_keeps_five_characters(self):
        key = "9" * 50
        item = {
            "NSU": 30,
            "ChaveAcesso": key,
            "TipoDocumento": "NFSE",
            "ArquivoXml": gzip_base64(nfse_xml(access_key=key, serie="49999")),
        }
        self.company._nfse_process_item(item)
        document = self._documents().filtered(lambda rec: rec.access_key == key)
        self.assertEqual(document.serie, "49999")

    def test_key_constraint_stays_active(self):
        document_model = self.env["l10n_br_fiscal.document"]
        names = [method.__name__ for method in document_model._constraint_methods]
        self.assertIn("_check_key", names)
        operation = self.env.ref("l10n_br_fiscal.fo_compras")
        nfse_vals = {
            "company_id": self.company.id,
            "partner_id": self.provider.id,
            "document_type_id": self.env.ref("l10n_br_fiscal.document_SE").id,
            "fiscal_operation_id": operation.id,
            "document_key": "2" * 50,
            "issuer": "partner",
            "document_number": "1",
        }
        document_model.create(nfse_vals)
        with self.assertRaises(ValidationError):
            document_model.create(dict(nfse_vals, document_number="2"))
        nfe_key = _nfe_access_key("3524015959431500015755001000000001112345678")
        nfe_vals = {
            "company_id": self.company.id,
            "partner_id": self.provider.id,
            "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
            "fiscal_operation_id": operation.id,
            "document_key": nfe_key,
            "issuer": "partner",
            "document_number": "1",
        }
        document_model.create(nfe_vals)
        with self.assertRaises(ValidationError):
            document_model.create(dict(nfe_vals, document_number="2"))


def _nfe_access_key(body):
    """43-digit NF-e key body plus the mod-11 check digit."""
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    total = 0
    for index, digit in enumerate(reversed(body)):
        total += int(digit) * weights[index % 8]
    rest = total % 11
    check = 0 if rest < 2 else 11 - rest
    return body + str(check)
