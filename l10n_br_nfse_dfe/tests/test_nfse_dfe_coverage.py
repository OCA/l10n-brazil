# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import datetime, timedelta, timezone
from unittest import mock

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_nfse_dfe.models.dfe_document import (
    L10nBrFiscalDfeDocument as NfseDfeDocument,
)
from odoo.addons.l10n_br_nfse_dfe.models.document import (
    L10nBrFiscalDocument as NfseDocument,
)
from odoo.addons.l10n_br_nfse_dfe.services.adn_dfe import AdnDfeClient
from odoo.addons.l10n_br_nfse_dfe.services.nfse_xml import (
    NfseNacionalBinding,
    decode_arquivo_xml,
    is_cancel_event,
    normalize_access_key,
    parse_nfse_datetime,
    parse_nfse_event_xml,
    parse_nfse_file,
    parse_nfse_xml,
    xml_root_is_nfse,
)
from odoo.addons.l10n_br_nfse_dfe.tests.test_nfse_dfe import (
    ACCESS_KEY,
    event_xml,
    gzip_base64,
    nfse_xml,
    response,
)


def _pkcs12_bytes(password=b"secret"):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "NFSe DF-e")])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(1)
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    return pkcs12.serialize_key_and_certificates(
        b"nfse",
        key,
        cert,
        None,
        serialization.BestAvailableEncryption(password),
    )


class TestNfseXmlEdges(TransactionCase):
    def test_decode_and_key_helpers(self):
        self.assertIsNone(decode_arquivo_xml(None))
        self.assertTrue(decode_arquivo_xml(b"<NFSe/>").startswith(b"<"))
        self.assertTrue(decode_arquivo_xml("<NFSe/>").startswith(b"<"))
        with mock.patch(
            "odoo.addons.l10n_br_nfse_dfe.services.nfse_xml.base64.b64decode",
            side_effect=ValueError("bad"),
        ):
            self.assertIsNone(decode_arquivo_xml("abc"))
            self.assertEqual(decode_arquivo_xml(b"abc"), b"abc")
        self.assertIsNone(decode_arquivo_xml(b"\x1f\x8bnot-gzip"))
        self.assertFalse(normalize_access_key(""))
        self.assertEqual(normalize_access_key("9" * 50), "9" * 50)
        self.assertEqual(normalize_access_key("abc" + "8" * 51), "8" * 50)
        self.assertFalse(normalize_access_key("123"))
        self.assertFalse(parse_nfse_datetime(""))
        self.assertFalse(parse_nfse_datetime("not-a-date"))
        parsed = parse_nfse_datetime("2026-01-02T03:04:05Z")
        self.assertEqual(parsed.hour, 3)
        self.assertIsNone(parse_nfse_xml(None))
        self.assertIsNone(parse_nfse_xml(b"<not-xml"))
        self.assertIsNone(parse_nfse_xml(b"<root/>"))
        self.assertIsNone(parse_nfse_file(None))
        self.assertFalse(is_cancel_event(""))
        self.assertTrue(is_cancel_event("e101101"))
        self.assertTrue(is_cancel_event("E105102"))
        self.assertFalse(is_cancel_event("999"))
        self.assertIsNone(parse_nfse_event_xml(None))
        self.assertIsNone(parse_nfse_event_xml(b"<not-xml"))
        self.assertIsNone(parse_nfse_event_xml(b"<root/>"))
        self.assertFalse(xml_root_is_nfse(None))
        self.assertFalse(xml_root_is_nfse(b"<not-xml"))
        self.assertTrue(xml_root_is_nfse(nfse_xml()))

    def test_parse_wrapped_note_and_split_ibs_value(self):
        key = "4" * 50
        split = f"""<NFSe><infNFSe Id="NFS{key}">
          <IBSCBS><totCIBS><gIBS>
            <gIBSUFTot><vIBSUF>1.00</vIBSUF></gIBSUFTot>
            <gIBSMunTot><vIBSMun>0.25</vIBSMun></gIBSMunTot>
          </gIBS></totCIBS></IBSCBS>
        </infNFSe></NFSe>""".encode()
        self.assertEqual(parse_nfse_xml(split)["ibs_value"], 1.25)
        nested = f"""<NFSe><wrap><infNFSe Id="NFS{key}"/></wrap></NFSe>""".encode()
        self.assertEqual(parse_nfse_xml(nested)["access_key"], key)
        bare = parse_nfse_xml(b"<NFSe></NFSe>")
        self.assertFalse(bare["access_key"])
        invalid_amount = (
            f'<NFSe><infNFSe Id="NFS{key}">'
            "<valores><vLiq>nope</vLiq></valores></infNFSe></NFSe>"
        ).encode()
        self.assertEqual(parse_nfse_xml(invalid_amount)["service_value"], 0.0)
        event = parse_nfse_event_xml(
            b"<evento><infPedReg><tpEvento>305101</tpEvento></infPedReg></evento>"
        )
        self.assertTrue(event["is_cancel"])


class TestNfseDfeCoverage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.company.nfse_dfe_environment = "producao_restrita"
        cls.company.nfse_dfe_next_query = False

    def test_dispatch_and_banner_actions(self):
        company = self.company
        self.assertEqual(
            company._dfe_cron_xmlid("nfse"),
            "l10n_br_nfse_dfe.ir_cron_search_nfse_dfe_documents",
        )
        company._dfe_cron_xmlid("nfe")
        self.assertEqual(
            company._dfe_document_action_xmlid("nfse"),
            "l10n_br_nfse_dfe.action_nfse_dfe_document",
        )
        company._dfe_document_action_xmlid("nfe")
        search = company.action_nfse_search_specific()
        self.assertEqual(search["context"]["default_fiscal_type"], "nfse")
        banner = self.env["res.company"].action_banner_specific_search_nfse()
        self.assertEqual(banner["res_model"], "dfe.specific.search.wizard")
        company_model = self.env["res.company"]
        with mock.patch.object(
            type(company), "action_document_distribution", return_value=None
        ):
            reloaded = company_model.action_banner_search_all_nfse()
        self.assertEqual(reloaded["tag"], "reload")
        window = {"type": "ir.actions.act_window"}
        with mock.patch.object(
            type(company), "action_document_distribution", return_value=window
        ):
            self.assertEqual(company_model.action_banner_search_all_nfse(), window)
        with mock.patch.object(
            type(company), "_nfse_document_distribution", return_value=None
        ) as nfse_loop:
            company.nfse_dfe_next_query = False
            company.action_nfse_document_distribution()
        nfse_loop.assert_called_once()
        parent = (
            "odoo.addons.l10n_br_fiscal_dfe.models.res_company."
            "ResCompany._dfe_search_specific_document"
        )
        with (
            mock.patch.object(
                type(company), "_nfse_search_specific", return_value=None
            ) as nfse_search,
            mock.patch(parent, return_value=None) as soap_search,
        ):
            company._dfe_search_specific_document("nfse", access_key=ACCESS_KEY)
            company._dfe_search_specific_document("cte", nsu="1")
        nfse_search.assert_called_once()
        soap_search.assert_called_once()

    def test_environment_and_query_without_cnpj(self):
        company = self.company
        company.nfse_dfe_environment = "producao"
        self.assertIn("adn.nfse.gov.br", company._nfse_adn_base_url())
        ghost = self.env["res.company"].new({"nfse_dfe_environment": False})
        self.assertIn("producaorestrita", ghost._nfse_adn_base_url())
        company.vat = False
        self.assertNotIn("cnpjConsulta", company._nfse_query_params())

    def test_certificate_and_request_cleanup(self):
        company = self.company
        with mock.patch.object(
            type(company), "_get_br_certificate", return_value=False
        ):
            with self.assertRaises(UserError):
                company._nfse_certificate_pem()
        certificate = mock.Mock()
        certificate.content = base64.b64encode(b"not-a-certificate")
        certificate.pkcs12_password = False
        certificate.with_context.return_value = certificate
        with (
            mock.patch.object(
                type(company), "_get_br_certificate", return_value=certificate
            ),
            mock.patch(
                "odoo.addons.l10n_br_nfse_dfe.models.res_company."
                "pkcs12.load_key_and_certificates",
                return_value=(None, None, None),
            ),
        ):
            with self.assertRaises(UserError):
                company._nfse_certificate_pem()
        certificate.pkcs12_password = "secret"
        certificate.content = base64.b64encode(_pkcs12_bytes())
        with mock.patch.object(
            type(company), "_get_br_certificate", return_value=certificate
        ):
            pem = company._nfse_certificate_pem()
        self.assertIn(b"BEGIN", pem)
        with (
            mock.patch.object(
                type(company), "_nfse_certificate_pem", return_value=b"pem"
            ),
            mock.patch(
                "odoo.addons.l10n_br_nfse_dfe.models.res_company.AdnDfeClient.get",
                return_value=response(200, {}),
            ),
            mock.patch(
                "odoo.addons.l10n_br_nfse_dfe.models.res_company.os.unlink",
                side_effect=OSError("already gone"),
            ),
        ):
            self.assertEqual(company._nfse_adn_request("/contribuintes/DFe/0").ok, True)

    def test_distribution_edges(self):
        company = self.company
        company.nfse_dfe_next_query = fields.Datetime.now() + timedelta(hours=1)
        with mock.patch.object(type(company), "_nfse_adn_request") as request:
            company._nfse_document_distribution()
        request.assert_not_called()

        company.nfse_dfe_next_query = False

        def explode(_company, path, params=None):
            raise RuntimeError("adn down")

        with mock.patch.object(type(company), "_nfse_adn_request", explode):
            company._nfse_document_distribution()
        self.assertFalse(company.nfse_dfe_last_status_code)
        company.nfse_dfe_next_query = False

        def empty(_company, path, params=None):
            return response(200, {})

        with mock.patch.object(type(company), "_nfse_adn_request", empty):
            company._nfse_document_distribution()
        self.assertEqual(company.nfse_dfe_last_status_code, "137")
        company.nfse_dfe_next_query = False

        def stuck(_company, path, params=None):
            return response(
                200,
                {
                    "LoteDFe": [
                        {
                            "NSU": 0,
                            "ChaveAcesso": ACCESS_KEY,
                            "TipoDocumento": "NFSE",
                            "ArquivoXml": base64.b64encode(nfse_xml()).decode(),
                        }
                    ]
                },
            )

        with mock.patch.object(type(company), "_nfse_adn_request", stuck):
            company._nfse_document_distribution()
        self.assertEqual(company.nfse_dfe_last_status_code, "138")
        company.nfse_dfe_next_query = False

        def rejected(_company, path, params=None):
            return response(
                500,
                {
                    "Erros": [
                        {"Codigo": "E1", "Descricao": "bad"},
                        "plain",
                    ]
                },
            )

        with mock.patch.object(type(company), "_nfse_adn_request", rejected):
            company._nfse_document_distribution()
        self.assertIn("E1", company.nfse_dfe_last_status)

        detail = company._nfse_error_detail(response(500, {"mensagem": "nope"}))
        self.assertEqual(detail, "nope")
        detail = company._nfse_error_detail(response(502, {}, headers={}))
        self.assertTrue(detail)
        self.assertEqual(
            len(company._nfse_lote(response(200, {"loteDFe": {"NSU": 1}}))), 1
        )
        self.assertEqual(
            company._nfse_retry_after_seconds(
                response(429, headers={"retry-after": "Wed, 21 Oct 2015 07:28:00 GMT"})
            ),
            0,
        )

        def rate_limit(_company, path, params=None):
            return response(
                429, headers={"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}
            )

        company.nfse_dfe_next_query = False
        with mock.patch.object(type(company), "_nfse_adn_request", rate_limit):
            company._nfse_document_distribution()
        self.assertEqual(company.nfse_dfe_last_status_code, "656")

    def test_skipped_and_duplicate_items(self):
        company = self.company
        company._nfse_create_note({"ChaveAcesso": "123"}, b"<NFSe></NFSe>", "1")
        company._nfse_create_event({"ChaveAcesso": "123"}, b"<evento/>", "2")
        note = {
            "NSU": 40,
            "ChaveAcesso": "5" * 50,
            "TipoDocumento": "NFSE",
            "ArquivoXml": base64.b64encode(nfse_xml(access_key="5" * 50)).decode(),
        }
        company._nfse_process_item(note)
        company._nfse_process_item(note)
        event = {
            "NSU": 41,
            "ChaveAcesso": "5" * 50,
            "TipoDocumento": "EVENTO",
            "TipoEvento": "101101",
            "ArquivoXml": base64.b64encode(event_xml(access_key="5" * 50)).decode(),
        }
        company._nfse_process_item(event)
        company._nfse_process_item(event)
        self.assertFalse(
            company._nfse_item_is_event(
                {
                    "TipoDocumento": "X",
                    "ArquivoXml": base64.b64encode(nfse_xml()).decode(),
                }
            )
        )
        self.assertTrue(
            company._nfse_item_is_event(
                {
                    "TipoDocumento": "X",
                    "ArquivoXml": base64.b64encode(event_xml()).decode(),
                }
            )
        )
        self.assertFalse(company._nfse_find_existing_dfe(False, False, "NFSe"))

    def test_specific_search_responses(self):
        company = self.company
        key = "2" * 50

        def sefin(_company, path):
            self.assertTrue(path.endswith(f"/nfse/{key}"))
            return response(
                200,
                {
                    "chaveAcesso": key,
                    "nfseXmlGZipB64": gzip_base64(nfse_xml(access_key=key)),
                },
            )

        def events(_company, path, params=None):
            self.assertTrue(path.endswith("/Eventos"))
            return response(
                200,
                {
                    "LoteDFe": [
                        {
                            "NSU": 8,
                            "ChaveAcesso": key,
                            "TipoDocumento": "NFSE",
                            "ArquivoXml": gzip_base64(nfse_xml(access_key=key)),
                        },
                        {
                            "NSU": 9,
                            "ChaveAcesso": key,
                            "TipoDocumento": "EVENTO",
                            "TipoEvento": "CANCELAMENTO",
                            "ArquivoXml": base64.b64encode(
                                event_xml(access_key=key)
                            ).decode(),
                        },
                    ]
                },
            )

        with (
            mock.patch.object(type(company), "_nfse_sefin_request", sefin),
            mock.patch.object(type(company), "_nfse_adn_request", events),
        ):
            company._nfse_search_specific(access_key=key)
        document = self.env["l10n_br_fiscal_dfe.document"].search(
            [("access_key", "=", key)], limit=1
        )
        self.assertTrue(document)
        self.assertEqual(document.document_state, "3")

        with mock.patch.object(
            type(company),
            "_nfse_sefin_request",
            return_value=response(200, {"mensagem": "empty"}),
        ):
            with self.assertRaises(UserError):
                company._nfse_search_specific(access_key="6" * 50)
        for status in (404, 429, 500):
            with mock.patch.object(
                type(company),
                "_nfse_sefin_request",
                return_value=response(status, {"message": "fail"}),
            ):
                with self.assertRaises(UserError):
                    company._nfse_search_specific(access_key="7" * 50)

        def by_nsu(_company, path, params=None):
            return response(
                200,
                {
                    "LoteDFe": [
                        {
                            "NSU": 15,
                            "ChaveAcesso": "8" * 50,
                            "TipoDocumento": "NFSE",
                            "ArquivoXml": base64.b64encode(
                                nfse_xml(access_key="8" * 50)
                            ).decode(),
                        }
                    ]
                },
            )

        with mock.patch.object(type(company), "_nfse_adn_request", by_nsu):
            company._nfse_search_specific(nsu="15")
            with self.assertRaises(UserError):
                company._nfse_search_specific(nsu="16")

    def test_event_label_import_and_duplicate_key(self):
        company = self.company
        dfe = self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "access_key": "7" * 50,
                "company_id": company.id,
                "fiscal_type": "nfse",
                "document_type_dfe": "event",
                "event_type_dfe": "E101101",
            }
        )
        self.assertEqual(dfe.event_type_dfe_label, "NFS-e Cancellation")
        dfe.event_type_dfe = False
        dfe._compute_event_type_dfe_label()
        dfe.event_type_dfe = "999999"
        dfe._compute_event_type_dfe_label()
        document = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "7" * 50,
                "company_id": company.id,
                "fiscal_type": "nfe",
                "document_state": "42",
            }
        )
        self.assertEqual(
            NfseDfeDocument._get_document_state_label(document),
            document.document_state,
        )
        caught = None
        try:
            NfseDfeDocument.import_document(document)
        except UserError as error:
            caught = error
        except NotImplementedError as error:
            caught = error
        self.assertIsNotNone(caught)
        nfse_key = "6" * 50
        nfse_doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": nfse_key,
                "company_id": company.id,
                "fiscal_type": "nfse",
                "vat": "",
            }
        )
        self.assertFalse(nfse_doc.partner_id)
        complete = self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "access_key": nfse_key,
                "company_id": company.id,
                "fiscal_type": "nfse",
                "document_type_dfe": "complete",
            }
        )
        nfse_doc.dfe_ids = [(4, complete.id)]
        complete.create_xml_attachment(nfse_xml(access_key=nfse_key))
        action = nfse_doc.import_document()
        self.assertEqual(action["res_model"], "l10n_br_fiscal.document.import.wizard")

        fiscal_vals = {
            "company_id": company.id,
            "partner_id": company.partner_id.id,
            "document_type_id": self.env.ref("l10n_br_fiscal.document_SE").id,
            "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_compras").id,
            "document_key": "4" * 50,
            "issuer": "partner",
        }
        self.env["l10n_br_fiscal.document"].create(fiscal_vals)
        try:
            duplicate = self.env["l10n_br_fiscal.document"].create(
                {**fiscal_vals, "document_number": "2"}
            )
        except ValidationError:
            duplicate = None
        if duplicate:
            with self.assertRaises(ValidationError):
                NfseDocument._check_key(duplicate)
        other = self.env["l10n_br_fiscal.document"].new({})
        NfseDocument._check_key(other)

    def test_import_wizard_fallbacks(self):
        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": self.company.id,
                "file": base64.b64encode(b"<NFe></NFe>"),
            }
        )
        parent_parse = (
            "odoo.addons.l10n_br_fiscal.wizards.document_import_wizard."
            "DocumentImportWizard._parse_file"
        )
        with mock.patch(parent_parse, return_value="parsed") as parsed:
            self.assertEqual(wizard._parse_file(), "parsed")
        parsed.assert_called_once()
        with self.assertRaises(UserError):
            wizard._detect_binding(object())
        wizard._extract_binding_data(object())
        with mock.patch.object(type(wizard), "_parse_file", return_value=object()):
            wizard._create_edoc_from_file()
        short_key = NfseNacionalBinding({"access_key": "1"})
        with mock.patch.object(type(wizard), "_parse_file", return_value=short_key):
            with self.assertRaises(UserError):
                wizard._create_edoc_from_file()
        imported = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": self.company.id,
                "file": base64.b64encode(nfse_xml(access_key="9" * 50)),
            }
        )
        imported.partner_id = False
        imported.issuer_partner_id = False
        imported._create_edoc_from_file()
        self.assertTrue(imported.document_id)
        self.assertFalse(wizard._nfse_find_service_type("12"))
        self.assertFalse(wizard._nfse_find_service_type("999999"))
        self.assertFalse(wizard._nfse_find_nbs(""))
        self.assertEqual(wizard._nfse_percent(0, 1), 0.0)
        self.assertEqual(wizard._nfse_percent(101, 0.5), 0.0)
        self.assertFalse(wizard._nfse_cst("pis", False))
        self.assertFalse(wizard._nfse_cst("pis", "ZZZ"))
        self.assertFalse(wizard._nfse_match_tax("l10n_br_fiscal.tax_group_issqn", 0.0))
        cst = self.env["l10n_br_fiscal.cst"].search([], limit=1)
        self.assertTrue(
            wizard._nfse_match_tax("l10n_br_fiscal.tax_group_issqn", 5.0, 0.0, cst)
        )
        self.assertFalse(wizard._nfse_amount_vals("issqn", 0, 0, 0, 0, False, False))
        self.assertEqual(wizard._nfse_percent(10, 0), 0.0)
        self.assertFalse(wizard._nfse_incidence_city(False))
        self.assertFalse(wizard._nfse_incidence_city("0000000"))
        with mock.patch.object(type(wizard.env), "ref", return_value=False):
            wizard._nfse_default_operation()
        search_wizard = self.env["dfe.specific.search.wizard"].create(
            {
                "company_id": self.company.id,
                "fiscal_type": "nfe",
                "search_type": "access_key",
            }
        )
        parent_validate = (
            "odoo.addons.l10n_br_fiscal_dfe.wizards.specific_search_wizard."
            "DfeSpecificSearchWizard._validate_access_key"
        )
        with mock.patch(parent_validate, return_value=None) as validate:
            search_wizard._validate_access_key("")
        validate.assert_called_once_with("")

    def test_adn_wrap_rejects_non_json(self):
        client = AdnDfeClient("https://adn.nfse.gov.br", "/tmp/unused.pem")
        broken = mock.Mock(status_code=200, content=b"[]", headers={}, text="[]")
        broken.json.side_effect = ValueError("no json")
        wrapped = client._wrap(broken)
        self.assertIsNone(wrapped.body)
        broken.json.side_effect = None
        broken.json.return_value = ["list"]
        self.assertIsNone(client._wrap(broken).body)
