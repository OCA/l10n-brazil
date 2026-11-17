# Copyright 2020 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import os
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from nfselib.barueri.nfse import NFSeRegistroTipo1, NFSeRegistroTipo2
from requests.exceptions import ConnectionError as RequestsConnectionError
from xmldiff import main

from odoo.exceptions import UserError
from odoo.tools import config

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_ENVIADA,
)
from odoo.addons.l10n_br_nfse.tests.test_fiscal_document_nfse_common import (
    TestFiscalDocumentNFSeCommon,
)

from ... import l10n_br_nfse_barueri

_logger = logging.getLogger(__name__)


class TestFiscalDocumentNFSeBarueri(TestFiscalDocumentNFSeCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.provedor_nfse = "barueri"
        cls.company.certificate_ecnpj_id = cls.env.company.certificate_ecnpj_id

    def test_nfse_barueri_xml_esperado(self):
        """Garante que o XML gerado para Barueri permaneça compatível com o esperado."""

        xml_path = os.path.join(
            l10n_br_nfse_barueri.__path__[0], "tests", "nfse", "nfse.xml"
        )

        self.nfse_same_state.rps_number = "50"
        self.nfse_same_state.document_number = "50"

        report_model = type(self.env["ir.actions.report"])
        with patch.object(
            report_model, "_render_qweb_pdf", return_value=(b"%PDF-1.4", "pdf")
        ) as render_pdf:
            self.nfse_same_state.action_document_confirm()

            self.nfse_same_state.document_date = datetime.strptime(
                "2020-06-04T11:58:46", "%Y-%m-%dT%H:%M:%S"
            )
            self.nfse_same_state.date_in_out = datetime.strptime(
                "2020-06-04T11:58:46", "%Y-%m-%dT%H:%M:%S"
            )

            self.nfse_same_state.with_context(lang="pt_BR")._document_export()

        output = os.path.join(
            config["data_dir"],
            "filestore",
            self.cr.dbname,
            self.nfse_same_state.send_file_id.store_fname,
        )
        _logger.info("XML file saved at %s", output)

        report = self.env.ref("l10n_br_nfse.report_br_nfse_danfe")
        render_pdf.assert_called_with(report, res_ids=self.nfse_same_state.ids)
        self.assertEqual(self.nfse_same_state.file_report_id.raw, b"%PDF-1.4")

        diff = main.diff_files(xml_path, output)
        _logger.info("Diff with expected XML (if any): %s", diff)

        # Espera-se no máximo pequenas diferenças irrelevantes
        self.assertLessEqual(len(diff), 1)

    def test_is_nfse_barueri_flag(self):
        """Valida o cálculo do campo técnico is_nfse_barueri."""
        barueri_city = self.env.ref("l10n_br_base.city_3505708")
        other_city = self.env.ref("l10n_br_base.city_3132404")

        self.company.city_id = barueri_city
        self.nfse_same_state.document_type = "SE"

        self.assertTrue(
            self.nfse_same_state.is_nfse_barueri,
        )

        self.company.city_id = other_city
        self.assertFalse(
            self.nfse_same_state.is_nfse_barueri,
        )

    def test_compute_url_nfse_barueri_ambientes(self):
        """Testa a geração da URL de consulta da
        NFSe em ambiente produção e homologação."""
        barueri_city = self.env.ref("l10n_br_base.city_3505708")
        self.company.city_id = barueri_city
        self.nfse_same_state.document_type = "SE"
        cnpj = self.nfse_same_state.partner_id.cnpj_cpf
        cnpj_without_punctuation = cnpj.translate(str.maketrans("", "", "./-"))
        self.nfse_same_state.verify_code = "ABC123"

        self.nfse_same_state.nfse_environment = "1"

        self.assertEqual(
            self.nfse_same_state.url_nfse_barueri,
            "https://www.barueri.sp.gov.br/nfe/wfimagemNota.aspx"
            f"?CODIGOAUTENTICIDADE=ABC123&NUMDOC={cnpj_without_punctuation}",
        )

        self.nfse_same_state.nfse_environment = "2"

        self.assertEqual(
            self.nfse_same_state.url_nfse_barueri,
            "https://testeeiss.barueri.sp.gov.br/nfe/wfimagemNota.aspx"
            f"?CODIGOAUTENTICIDADE=ABC123&NUMDOC={cnpj_without_punctuation}",
        )

    def test_action_open_nfse_barueri(self):
        """Garante que a ação de abrir a NFSe retorna um ir.actions.act_url válido."""
        barueri_city = self.env.ref("l10n_br_base.city_3505708")
        self.company.city_id = barueri_city
        self.nfse_same_state.document_type = "SE"
        self.nfse_same_state.verify_code = "COD123"
        self.nfse_same_state.nfse_environment = "1"

        action = self.nfse_same_state.action_open_nfse_barueri()

        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertTrue(action["url"])
        self.assertEqual(action["url"], self.nfse_same_state.url_nfse_barueri)
        self.assertEqual(action["target"], "new")

    def test_serialize_barueri_lote_rps_retorna_bytes(self):
        """Verifica que o lote RPS gerado para
        Barueri é retornado em bytes e não vazio."""
        barueri_city = self.env.ref("l10n_br_base.city_3505708")
        self.company.city_id = barueri_city
        self.nfse_same_state.document_type = "SE"

        now = datetime.now()
        self.nfse_same_state.document_date = now
        self.nfse_same_state.date_in_out = now

        rps_bytes = self.nfse_same_state._serialize_barueri_lote_rps()

        self.assertIsInstance(rps_bytes, (bytes, bytearray))
        self.assertTrue(rps_bytes, "O conteúdo do RPS não deveria ser vazio.")

    def test_baixar_xml_nfse_monta_url_corretamente(self):
        """Garante que o método de download de
        XML monta a URL esperada e trata o retorno."""
        autenticidade = "ABC123"
        cnpj = "12345678000195"

        for environment, host in (
            ("1", "www.barueri.sp.gov.br"),
            ("2", "testeeiss.barueri.sp.gov.br"),
        ):
            with self.subTest(environment=environment), patch(
                "odoo.addons.l10n_br_nfse_barueri.models.document.requests.get"
            ) as mock_get:
                self.nfse_same_state.nfse_environment = environment
                mock_get.return_value.text = "<xml/>"

                result = self.nfse_same_state._baixar_xml_nfse(autenticidade, cnpj)

                mock_get.assert_called_once_with(
                    f"https://{host}/nfe/xmlNFe.ashx"
                    "?codigoautenticidade=ABC123&numdoc=12345678000195",
                    timeout=15,
                )
                mock_get.return_value.raise_for_status.assert_called_once()
                self.assertEqual(result, "<xml/>")

    def _barueri_document_with_receipt(self):
        document = self.nfse_same_state
        document.authorization_event_id = document.event_ids.create_event_save_xml(
            company_id=document.company_id,
            environment=EVENT_ENV_HML,
            event_type="0",
            xml_file="<rps/>",
            document_id=document,
        )
        document.authorization_event_id.lot_receipt_number = "123"
        return document

    def _barueri_return_file(self, status):
        record = NFSeRegistroTipo2()
        record.campos[2].valor = "55"
        record.campos[3].valor = "20260101"
        record.campos[4].valor = "110001"
        record.campos[5].valor = "ABC123"
        record.campos[10].valor = status
        record.campos[14].valor = "12345678000195"
        header = NFSeRegistroTipo1()
        return "\n".join((header.exportar(), record.exportar())).encode("latin1")

    def test_retry_download_without_resending_the_rps(self):
        document = self._barueri_document_with_receipt()
        document.authorization_event_id.lot_receipt_number = False
        document.write(
            {
                "state_edoc": SITUACAO_EDOC_A_ENVIAR,
                "document_date": datetime(2020, 6, 4, 11, 58, 46),
                "date_in_out": datetime(2020, 6, 4, 11, 58, 46),
            }
        )
        processor = MagicMock()
        processor.processar_documento.return_value = [
            SimpleNamespace(
                webservice="NFeLoteEnviarArquivo",
                resposta=SimpleNamespace(ProtocoloRemessa="123"),
            ),
            SimpleNamespace(
                webservice="NFeLoteStatusArquivo",
                resposta=SimpleNamespace(
                    ListaNfeArquivosRPS=SimpleNamespace(
                        SituacaoArq="-1", NomeArqRetorno="123.txt"
                    )
                ),
            ),
        ]
        processor.analisa_retorno_consulta.return_value = (1, "Processed")
        consulta = processor.consulta_nfse_rps.return_value
        consulta.resposta.ListaNfeArquivosRPS.NomeArqRetorno = "123.txt"
        processor.baixar_lote_rps.return_value.retorno.ArquivoRPSBase64 = (
            self._barueri_return_file("A")
        )

        with patch.object(
            type(document), "_processador_erpbrasil_nfse", return_value=processor
        ), patch.object(
            type(document),
            "_baixar_xml_nfse",
            side_effect=[RequestsConnectionError("unavailable"), "<nfse/>"],
        ), patch.object(type(document), "make_pdf"):
            document.action_document_send()
            self.assertEqual(document.state_edoc, SITUACAO_EDOC_ENVIADA)
            self.assertEqual(document.authorization_event_id.lot_receipt_number, "123")

            document._cron_document_status_barueri()
            self.assertEqual(document.state_edoc, SITUACAO_EDOC_ENVIADA)
            self.assertEqual(document.status_code, "-1")
            self.assertEqual(document.document_number, "0000055")
            self.assertEqual(document.verify_code, "ABC123")
            self.assertEqual(document.edoc_error_message, "unavailable")

            document.action_document_send()

        processor.processar_documento.assert_called_once()
        self.assertEqual(document.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(document.authorization_file_id.raw, b"<nfse/>")
        self.assertFalse(document.edoc_error_message)

    def test_cancellation_waits_for_batch_confirmation(self):
        document = self._barueri_document_with_receipt()
        document.state_edoc = SITUACAO_EDOC_AUTORIZADA
        processor = MagicMock()
        processor.envia_documento.return_value.resposta.ProtocoloRemessa = "456"
        processor.analisa_retorno_consulta.return_value = (-2, "Pending")

        with patch.object(
            type(document), "_processador_erpbrasil_nfse", return_value=processor
        ), patch.object(type(document), "serialize_nfse_barueri") as serialize:
            document._document_cancel("Justificativa para cancelar a NFS-e")

        serialize.assert_called_once_with(cancel=True)
        processor.envia_documento.assert_called_once()
        processor.processar_documento.assert_not_called()
        self.assertEqual(document.state_edoc, SITUACAO_EDOC_ENVIADA)
        self.assertEqual(document.status_code, "-2")
        self.assertEqual(document.authorization_event_id.lot_receipt_number, "456")
        self.assertFalse(document.cancel_event_id)
        with self.assertRaises(UserError):
            document.action_document_cancel()

        processor.analisa_retorno_consulta.return_value = (1, "Processed")
        processor.baixar_lote_rps.return_value.retorno.ArquivoRPSBase64 = (
            self._barueri_return_file("C")
        )
        with patch.object(
            type(document), "_processador_erpbrasil_nfse", return_value=processor
        ), patch.object(
            type(document), "_baixar_xml_nfse", return_value="<cancelled/>"
        ), patch.object(type(document), "cancel_move_ids") as cancel_moves:
            document._cron_document_status_barueri()

        cancel_moves.assert_called_once()
        self.assertEqual(document.state_edoc, SITUACAO_EDOC_CANCELADA)
        self.assertEqual(document.cancel_event_id.state, "done")
        self.assertEqual(document.cancel_event_id.protocol_number, "456")

    def test_rejected_cancellation_preserves_authorization(self):
        document = self._barueri_document_with_receipt()
        document.authorization_event_id.state = "done"
        document.write({"state_edoc": SITUACAO_EDOC_ENVIADA, "status_code": "-2"})
        processor = MagicMock()
        processor.analisa_retorno_consulta.return_value = (2, "Rejected")
        processor.baixar_lote_rps.return_value.resposta.ListaMensagemRetorno = (
            SimpleNamespace(
                Codigo="R1", Mensagem="Cancellation rejected", Correcao="Try again"
            )
        )

        with patch.object(
            type(document), "_processador_erpbrasil_nfse", return_value=processor
        ):
            document._cron_document_status_barueri()

        self.assertEqual(document.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertFalse(document.cancel_event_id)
        self.assertIn("Cancellation rejected", document.edoc_error_message)

    def test_danfse_report_renders_with_and_without_city_logo(self):
        document = self.nfse_same_state
        report = self.env.ref("l10n_br_nfse.report_br_nfse_danfe")
        self.assertTrue(self.company.logo)
        for city_logo in (False, self.company.logo):
            with self.subTest(has_city_logo=bool(city_logo)):
                self.company.nfse_city_logo = city_logo
                html, _render_type = report._render_qweb_html(report, document.ids)
                self.assertIn(b"NOTA FISCAL ELETR", html)
                self.assertEqual(html.count(b"data:image/"), 2 if city_logo else 1)
