# Copyright 2020 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import os
from datetime import datetime
from unittest.mock import patch

from xmldiff import main

from odoo.exceptions import UserError
from odoo.tools import config

from odoo.addons.l10n_br_fiscal.constants.fiscal import EVENT_ENV_PROD
from odoo.addons.l10n_br_nfse.tests.test_fiscal_document_nfse_common import (
    TestFiscalDocumentNFSeCommon,
)

from ... import l10n_br_nfse_paulistana

_logger = logging.getLogger(__name__)


class TestFiscalDocumentNFSePaulistana(TestFiscalDocumentNFSeCommon):
    def setUp(self):
        super().setUp()
        self.company.provedor_nfse = "paulistana"

        self.nfse_same_state.nfse_environment = "1"

    @staticmethod
    def _build_nfse_ok_xml():
        return """
        <RetornoConsulta xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                         xmlns="http://www.prefeitura.sp.gov.br/nfe">
            <Cabecalho xmlns="" Versao="1">
                <Sucesso>true</Sucesso>
            </Cabecalho>
            <NFe xmlns="">
                <ChaveNFe>
                    <InscricaoPrestador>56816600</InscricaoPrestador>
                    <NumeroNFe>123</NumeroNFe>
                    <CodigoVerificacao>ABC123</CodigoVerificacao>
                </ChaveNFe>
                <DataEmissaoRPS>2020-01-01</DataEmissaoRPS>
            </NFe>
        </RetornoConsulta>
        """

    @staticmethod
    def _build_nfse_error_xml():
        return """
        <RetornoConsulta xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                         xmlns="http://www.prefeitura.sp.gov.br/nfe">
            <Cabecalho xmlns="" Versao="1">
                <Sucesso>false</Sucesso>
            </Cabecalho>
            <Erro>
                <Codigo>001</Codigo>
                <Descricao>Erro de teste</Descricao>
            </Erro>
        </RetornoConsulta>
        """

    @staticmethod
    def _build_cancelamento_xml():
        return """
        <PedidoCancelamentoNFe xmlns="http://www.prefeitura.sp.gov.br/nfe">
            <Cabecalho xmlns="" Versao="1">
                <CPFCNPJRemetente>
                    <CNPJ>26030112000189</CNPJ>
                </CPFCNPJRemetente>
                <transacao>true</transacao>
            </Cabecalho>
            <Detalhe xmlns="">
                <ChaveNFe>
                    <InscricaoPrestador>56816600</InscricaoPrestador>
                    <NumeroNFe>123</NumeroNFe>
                    <CodigoVerificacao>ABC123</CodigoVerificacao>
                </ChaveNFe>
                <AssinaturaCancelamento>ASSINATURA_FAKE</AssinaturaCancelamento>
            </Detalhe>
        </PedidoCancelamentoNFe>
        """

    @staticmethod
    def _fake_processador_envio_sucesso():
        class FakeCabecalho:
            def __init__(self, sucesso):
                self.Sucesso = sucesso

        class FakeResposta:
            def __init__(self, sucesso=True):
                self.Cabecalho = FakeCabecalho(sucesso)

        class FakeProcesso:
            def __init__(self, webservice, retorno, sucesso=True):
                self.webservice = webservice
                self.retorno = retorno
                self.resposta = FakeResposta(sucesso)
                self.envio_xml = (
                    TestFiscalDocumentNFSePaulistana._build_cancelamento_xml()
                )

        class FakeProcessador:
            def __init__(self, processo):
                self._processo = processo

            def processar_documento(self, _edoc):
                yield self._processo

            def consulta_nfse_rps(self, **_kwargs):
                return self._processo

            def analisa_retorno_consulta(self, _processo):
                return "NFSe autorizada"

            def cancela_documento(self, doc_numero):
                return self._processo

            def analisa_retorno_cancelamento_paulistana(
                self,
                _processo,
            ):
                return True, "Cancelamento efetuado"

        processo = FakeProcesso(
            webservice="EnvioLoteRPS",
            retorno=TestFiscalDocumentNFSePaulistana._build_nfse_ok_xml(),
            sucesso=True,
        )
        return FakeProcessador(processo)

    @staticmethod
    def _fake_processador_cancelamento_falha():
        class FakeCabecalho:
            def __init__(self, sucesso):
                self.Sucesso = sucesso

        class FakeResposta:
            def __init__(self, sucesso=False):
                self.Cabecalho = FakeCabecalho(sucesso)

        class FakeProcesso:
            def __init__(self, webservice, retorno, sucesso=False):
                self.webservice = webservice
                self.retorno = retorno
                self.resposta = FakeResposta(sucesso)
                self.envio_xml = (
                    TestFiscalDocumentNFSePaulistana._build_cancelamento_xml()
                )

        class FakeProcessador:
            def __init__(self, processo):
                self._processo = processo

            def cancela_documento(self, doc_numero):
                return self._processo

            def analisa_retorno_cancelamento_paulistana(
                self,
                _processo,
            ):
                return False, "Erro ao cancelar"

        processo = FakeProcesso(
            webservice="EnvioLoteRPS",
            retorno=TestFiscalDocumentNFSePaulistana._build_nfse_error_xml(),
            sucesso=False,
        )
        return FakeProcessador(processo)

    def test_nfse_paulistana(self):
        """Test NFS-e same state."""

        xml_path = os.path.join(
            l10n_br_nfse_paulistana.__path__[0], "tests", "nfse", "paulistana.xml"
        )

        self.nfse_same_state.rps_number = "50"
        self.nfse_same_state.document_number = "50"

        with patch(
            "odoo.addons.l10n_br_nfse.models.document.Document.make_pdf",
            return_value=None,
        ):
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

        diff = main.diff_files(xml_path, output)
        _logger.info("Diff with expected XML (if any): %s", diff)

        assert len(diff) == 0

    def test_eletronic_document_send_envio_lote_sucesso(self):
        document = self.nfse_same_state
        document.authorization_event_id = False

        with patch(
            "odoo.addons.l10n_br_nfse.models.document.Document.make_pdf",
            return_value=None,
        ):
            document.action_document_confirm()

        document.document_date = datetime.strptime(
            "2020-06-04T11:58:46", "%Y-%m-%dT%H:%M:%S"
        )
        document.date_in_out = datetime.strptime(
            "2020-06-04T11:58:46", "%Y-%m-%dT%H:%M:%S"
        )

        with patch(
            "odoo.addons.l10n_br_nfse.models.document.Document._processador_erpbrasil_nfse",
            return_value=self._fake_processador_envio_sucesso(),
        ):
            document._eletronic_document_send()

        self.assertEqual(document.status_code, "4")
        self.assertEqual(document.status_name, "Procesado com Sucesso")
        self.assertEqual(document.edoc_error_message, "")

    def test_document_status_consulta_sucesso(self):
        document = self.nfse_same_state
        with patch(
            "odoo.addons.l10n_br_nfse.models.document.Document.make_pdf",
            return_value=None,
        ):
            document.action_document_confirm()

        event = document.event_ids.create_event_save_xml(
            company_id=document.company_id,
            environment=EVENT_ENV_PROD,
            event_type="0",
            xml_file="<xml/>",
            document_id=document,
        )
        document.authorization_event_id = event

        fake_processador = self._fake_processador_envio_sucesso()
        fake_processador._processo.webservice = "ConsultaLote"

        with patch(
            "odoo.addons.l10n_br_nfse.models.document.Document._processador_erpbrasil_nfse",
            return_value=fake_processador,
        ):
            status = document._document_status()

        self.assertEqual(document.document_number, "123")
        self.assertEqual(
            document.verify_code,
            "ABC123",
        )
        self.assertEqual(document.status_code, "4")
        self.assertEqual(document.status_name, "Procesado com Sucesso")
        self.assertEqual(document.edoc_error_message, "")
        self.assertEqual(status, "NFSe autorizada")

    def test_cancel_document_paulistana_sucesso(self):
        document = self.nfse_same_state
        document.document_number = "123"
        document.verify_code = "ABC123"
        document.nfse_environment = "1"

        with patch(
            "odoo.addons.l10n_br_nfse.models.document.Document._processador_erpbrasil_nfse",
            return_value=self._fake_processador_envio_sucesso(),
        ):
            result = document.cancel_document_paulistana()

        self.assertTrue(result)
        self.assertTrue(document.cancel_event_id)

    def test_cancel_document_paulistana_falha(self):
        document = self.nfse_same_state
        document.document_number = "123"
        document.verify_code = "ABC123"
        document.nfse_environment = "1"

        with patch(
            "odoo.addons.l10n_br_nfse.models.document.Document._processador_erpbrasil_nfse",
            return_value=self._fake_processador_cancelamento_falha(),
        ):
            with self.assertRaises(UserError):
                document.cancel_document_paulistana()

    def test_before_document_cancel_chama_cancelamento(self):
        document = self.nfse_same_state

        with patch.object(
            type(document),
            "cancel_document_paulistana",
            autospec=True,
        ) as mock_cancel:
            document._before_document_cancel()

        mock_cancel.assert_called_once_with(document)

    def test_before_document_cancel_documento_nao_paulistana(self):
        document = self.nfse_same_state
        document.company_id.provedor_nfse = False

        with patch.object(
            type(document),
            "cancel_document_paulistana",
            autospec=True,
        ) as mock_cancel:
            result = document._before_document_cancel()

        mock_cancel.assert_not_called()
        self.assertTrue(result)
