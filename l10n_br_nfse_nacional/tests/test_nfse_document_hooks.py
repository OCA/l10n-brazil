# Copyright 2026 Pop Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import gzip
from types import SimpleNamespace
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import TransactionCase
from odoo.tools import mute_logger

from odoo.addons.l10n_br_fiscal_edi.models.document import (
    Document as EdiDocument,
)
from odoo.addons.l10n_br_nfse.models.document import Document as NfseDocument

from ..constants.nfse_nacional import DANFSE_NACIONAL_TEMPLATE
from ..transport.adn_rest import AdnRestClient
from .common import set_provedor_nacional

DOCUMENT_LOGGER = "odoo.addons.l10n_br_nfse_nacional.models.document"


class TestNfseDocumentHooks(TransactionCase):
    """Hooks of the national NFS-e that the DPS export tests do not reach."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document = cls.env.ref("l10n_br_nfse_nacional.demo_nfse_lc")
        set_provedor_nacional(cls.document)
        cls.line = cls.document.fiscal_line_ids[0]
        cls.Document = type(cls.document)

    def _other_provider(self):
        self.document.company_id.provedor_nfse = False

    def test_a_mei_company_declares_the_mei_option(self):
        company = self.document.company_id
        company.tax_framework = "4"
        self.assertEqual(company.nfse10_opSimpNac, "2")
        self.assertFalse(company.nfse10_regApTribSN)
        self.assertEqual(company.nfse10_regEspTrib, "0")

    def test_the_weighted_rate_of_a_document_without_value_is_zero(self):
        empty = self.env["l10n_br_fiscal.document"].new({})
        self.assertEqual(empty._nfse10_weighted_percent("issqn_percent"), 0.0)

    def test_a_service_with_issqn_not_taxed_is_declared_so(self):
        line = SimpleNamespace(
            issqn_eligibility=False,
            issqn_tax_id=self.env.ref("l10n_br_fiscal.tax_issqn_nt"),
        )
        self.assertEqual(self.document._nfse10_trib_issqn_code(line), "4")

    @mute_logger(DOCUMENT_LOGGER)
    def test_lines_with_different_codes_only_warn_without_consolidation(self):
        self.document.nfse_nacional_concat_lines = False
        with mock.patch.object(
            self.Document,
            "_nfse10_service_mismatches",
            return_value=["cTribNac: a -> 1, b -> 2"],
        ):
            self.document._check_nfse_service_consistency()
            self.document.nfse_nacional_concat_lines = True
            with self.assertRaises(UserError):
                self.document._check_nfse_service_consistency()

    def test_a_document_without_service_line_keeps_its_values(self):
        with (
            mock.patch.object(
                self.Document, "_nfse10_service_line", return_value=self.line.browse()
            ),
            mock.patch.object(
                self.Document, "_check_nfse_service_consistency"
            ) as check,
        ):
            self.document._prepare_nfse10_service()
        check.assert_not_called()

    def test_a_document_without_date_has_no_emission_date(self):
        empty = self.env["l10n_br_fiscal.document"].new({})
        empty._compute_nfse10_dates()
        self.assertFalse(empty.nfse10_dhEmi)
        self.assertFalse(empty.nfse10_dCompet)

    def test_other_providers_keep_the_shared_hooks(self):
        self._other_provider()
        self.assertEqual(
            self.document._nfse_ibscbs_line(), self.document.fiscal_line_ids[:1]
        )
        with mock.patch.object(
            NfseDocument, "_processador_erpbrasil_nfse", return_value="municipal"
        ):
            self.assertEqual(self.document._processador_erpbrasil_nfse(), "municipal")

    def test_the_adn_is_not_a_municipal_processor(self):
        self.assertIsNone(self.document._processador_erpbrasil_nfse())

    def test_the_xml_of_another_provider_is_validated_as_usual(self):
        self._other_provider()
        with mock.patch.object(EdiDocument, "_validate_xml") as validate:
            self.document._validate_xml("<xml/>")
        validate.assert_called_once()

    def test_the_event_environment_follows_the_document(self):
        self.document.nfse_environment = "1"
        self.assertEqual(self.document._nfse_nacional_event_env(), "prod")
        self.document.nfse_environment = "2"
        self.assertEqual(self.document._nfse_nacional_event_env(), "hml")

    def test_xml_tags_of_the_adn_answer(self):
        tag = self.Document._adn_xml_tag
        self.assertEqual(tag("<a><nNFSe>12</nNFSe></a>", "nNFSe"), "12")
        self.assertFalse(tag("<a/>", "nNFSe"))
        self.assertFalse(tag("", "nNFSe"))

    def test_a_plain_nfse_xml_in_the_answer(self):
        self.assertEqual(
            self.Document._adn_decode_nfse({"nfseXml": "<NFSe/>"}), "<NFSe/>"
        )
        self.assertEqual(self.Document._adn_decode_nfse({}), "")

    def test_an_answer_without_error_list_shows_its_message(self):
        response = SimpleNamespace(body={"mensagem": "Fora do ar"}, content=b"")
        self.assertEqual(self.Document._adn_format_errors(response), "Fora do ar")
        response = SimpleNamespace(body=None, content=b"Bad gateway")
        self.assertEqual(self.Document._adn_format_errors(response), "Bad gateway")

    def test_a_cancellation_refused_by_the_adn(self):
        response = SimpleNamespace(
            status_code=400,
            body={"erros": [{"Codigo": "E1", "Descricao": "Prazo"}]},
            content=b"",
        )
        with self.assertRaises(UserError):
            self.document._adn_process_cancel_response(response, "<x/>")

    def test_only_an_authorized_note_is_checked_at_the_adn(self):
        self.document.state_edoc = "em_digitacao"
        with mock.patch.object(self.Document, "_adn_post") as post:
            self.document._adn_check_cancellation_status()
        post.assert_not_called()

    def test_the_danfse_has_no_html_rendering(self):
        report = self.env["ir.actions.report"]
        self.assertIsNone(
            report._render_qweb_html(DANFSE_NACIONAL_TEMPLATE, self.document.ids)
        )
        html = report._render_qweb_html(
            "base.report_ir_model_overview", self.env.ref("base.model_res_partner").ids
        )
        self.assertTrue(html[0])

    def test_the_client_resolves_a_dps_id(self):
        client = AdnRestClient("https://sefin.example.gov.br/SefinNacional/", "c.pem")
        answer = mock.Mock(status_code=200, content=b"{}")
        answer.json.return_value = {"chaveAcesso": "123"}
        with mock.patch.object(client._session, "get", return_value=answer) as get:
            response = client.get_dps("DPS1")
        self.assertEqual(response.body, {"chaveAcesso": "123"})
        self.assertTrue(get.call_args[0][0].endswith("/SefinNacional/dps/DPS1"))

    def test_a_gzipped_nfse_in_the_answer(self):
        raw = base64.b64encode(gzip.compress(b"<NFSe/>")).decode()
        self.assertEqual(
            self.Document._adn_decode_nfse({"nfseXmlGZipB64": raw}), "<NFSe/>"
        )

    def test_cancelling_sends_the_event_with_the_chosen_motive(self):
        with (
            mock.patch.object(self.Document, "_adn_cancel") as cancel,
            mock.patch.object(EdiDocument, "_document_cancel") as parent,
        ):
            self.document.with_context(nfse_cancel_motive="2")._document_cancel(
                "Servico nao prestado"
            )
        cancel.assert_called_once_with("Servico nao prestado", "2")
        parent.assert_called_once()

    def test_the_pdf_of_another_provider_is_left_to_it(self):
        self._other_provider()
        with mock.patch.object(NfseDocument, "make_pdf") as make_pdf:
            self.document.make_pdf()
        make_pdf.assert_called_once()

    def test_the_dps_number_comes_from_the_rps_number(self):
        with (
            mock.patch.object(EdiDocument, "_document_number", return_value=None),
            mock.patch.object(self.Document, "_nfse_nacional_generate_key") as generate,
        ):
            self.document.write(
                {"document_number": False, "document_key": False, "rps_number": "42"}
            )
            self.document._document_number()
            self.assertEqual(self.document.document_number, "42")
            generate.assert_called_once()
            generate.reset_mock()
            self.document.issuer = "partner"
            self.document._document_number()
            self._other_provider()
            self.document._document_number()
        generate.assert_not_called()
