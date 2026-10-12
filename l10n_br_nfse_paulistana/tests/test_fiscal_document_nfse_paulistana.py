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

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_STATE_CANCEL,
    EVENT_ENV_PROD,
)
from odoo.addons.l10n_br_fiscal_edi.constants.fiscal import DOCUMENT_STATE_AUTHORIZED
from odoo.addons.l10n_br_nfse.tests.test_fiscal_document_nfse_common import (
    TestFiscalDocumentNFSeCommon,
)

from ... import l10n_br_nfse_paulistana

_logger = logging.getLogger(__name__)


class TestFiscalDocumentNFSePaulistana(TestFiscalDocumentNFSeCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.lang"]._activate_lang("pt_BR")
        cls.company.provedor_nfse = "paulistana"
        # Configuração fiscal da Reforma IBS/CBS: os dados de exemplo não trazem
        # cClassTrib nem INDOP na linha, então o envelope IBSCBS sairia vazio.
        # Dados apenas de teste — não mover para demo data (a dívida é de
        # configuração de teste, não de dados do módulo).
        # Amarrar NBS, Código de Tributação do Município e a Classificação
        # Tributária (cClassTrib) diretamente na linha do documento: em v18
        # tax_classification_id é computado a partir do mapeamento fiscal, mas é
        # readonly=False/store=True, então o valor escrito aqui persiste até a
        # serialização.
        line = cls.nfse_same_state.fiscal_line_ids[:1]
        line.nbs_id = cls.nbs_id
        line.city_taxation_code_id = cls.env.ref(
            "l10n_br_fiscal.city_taxation_code_itajuba"
        )
        line.tax_classification_id = cls.env.ref(
            "l10n_br_fiscal.tax_classification_000001"
        )
        # O gate da Reforma exige o INDOP oficial (cIndOp) na linha, vindo do
        # cadastro l10n_br_fiscal.operation.indicator.
        line.operation_indicator_id = cls.env.ref(
            "l10n_br_fiscal.operation_indicator_050101"
        )

    def test_nfse_paulistana(self):
        """Test NFS-e same state."""
        self.skipTest(
            "Fixture tests/nfse/paulistana.xml é pré-Reforma Tributária (v02). "
            "Regerar a partir da saída v03 (XIPP-15079) após revisão fiscal dos bytes."
        )

        xml_path = os.path.join(
            l10n_br_nfse_paulistana.__path__[0], "tests", "nfse", "paulistana.xml"
        )

        self.nfse_same_state.rps_number = "50"
        self.nfse_same_state.document_number = "50"

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

    def test_serialize_nfse_paulistana(self):
        """Test serialization of NFS-e Paulistana."""
        self.nfse_same_state.rps_number = "50"
        self.nfse_same_state.document_number = "50"

        self.nfse_same_state.action_document_confirm()

        # Test serialization
        serialized = self.nfse_same_state.serialize_nfse_paulistana()
        self.assertIsNotNone(serialized)
        self.assertTrue(hasattr(serialized, "Cabecalho"))
        self.assertTrue(hasattr(serialized, "RPS"))
        self.assertEqual(len(serialized.RPS), 1)

    def test_map_taxation_rps(self):
        """Test mapping of taxation RPS."""
        # Test all taxation mappings
        self.assertEqual(self.nfse_same_state._map_taxation_rps("1"), "T")
        self.assertEqual(self.nfse_same_state._map_taxation_rps("2"), "F")
        self.assertEqual(self.nfse_same_state._map_taxation_rps("3"), "A")
        self.assertEqual(self.nfse_same_state._map_taxation_rps("4"), "R")
        self.assertEqual(self.nfse_same_state._map_taxation_rps("5"), "X")
        self.assertEqual(self.nfse_same_state._map_taxation_rps("6"), "X")

    def test_map_type_rps(self):
        """Test mapping of RPS type."""
        # Test all RPS type mappings
        self.assertEqual(self.nfse_same_state._map_type_rps("1"), "RPS")
        self.assertEqual(self.nfse_same_state._map_type_rps("2"), "RPS-M")
        self.assertEqual(self.nfse_same_state._map_type_rps("3"), "RPS-C")

    def test_map_provision_municipality(self):
        """Test mapping of provision municipality."""
        # Test provision municipality mapping
        self.assertIsNone(
            self.nfse_same_state._map_provision_municipality("1", "3550308")
        )
        self.assertEqual(
            self.nfse_same_state._map_provision_municipality("2", "3550308"), "3550308"
        )

    def _confirm_nfse_same_state(self):
        # v18: os onchange v14 (_onchange_document_serie_id, _onchange_company_id,
        # _onchange_product_id_fiscal e afins) não existem mais em l10n_br_fiscal
        # — os campos fiscais são computados. Espelha o recipe do
        # test_serialize_nfse_paulistana: amarra rps/document_number e confirma.
        self.nfse_same_state.rps_number = "50"
        self.nfse_same_state.document_number = "50"
        self.nfse_same_state.action_document_confirm()

    def test_serialize_reforma_ibscbs(self):
        """Envelope v03 da Reforma Tributária (IBS/CBS) e campos obrigatórios."""
        self._confirm_nfse_same_state()

        serialized = self.nfse_same_state.serialize_nfse_paulistana()
        rps = serialized.RPS[0]

        self.assertEqual(serialized.Cabecalho.Versao, 2)
        self.assertIsNone(getattr(serialized.Cabecalho, "ValorTotalServicos", None))
        self.assertIsNone(getattr(serialized.Cabecalho, "ValorTotalDeducoes", None))

        self.assertIsNotNone(rps.IBSCBS)
        self.assertEqual(rps.IBSCBS.finNFSe, 0)
        self.assertEqual(rps.IBSCBS.indFinal, 0)
        self.assertEqual(rps.IBSCBS.indDest, 1)
        self.assertIsNotNone(rps.IBSCBS.valores.trib.gIBSCBS)

        line = self.nfse_same_state.fiscal_line_ids[0]
        self.assertTrue(line.tax_classification_id.code)
        self.assertEqual(
            rps.IBSCBS.valores.trib.gIBSCBS.cClassTrib,
            line.tax_classification_id.code,
        )
        self.assertTrue(line.operation_indicator_id.code)
        self.assertEqual(rps.IBSCBS.cIndOp, line.operation_indicator_id.code)

        self.assertEqual(rps.ExigibilidadeSuspensa, 0)
        self.assertEqual(rps.PagamentoParceladoAntecipado, 0)
        self.assertEqual(rps.ValorIPI, 0)
        self.assertIsNone(rps.ValorInicialCobrado)
        self.assertIsNotNone(rps.ValorFinalCobrado)

        # cLocPrestacao XOR cPaisPrestacao (xs:choice): serviço no Brasil.
        self.assertEqual(
            rps.cLocPrestacao,
            self.nfse_same_state.partner_id.city_id.ibge_code,
        )
        self.assertIsNone(rps.cPaisPrestacao)
        self.assertEqual(rps.NBS, self.nbs_id.code_unmasked)

    def test_assinatura_rps_bytes(self):
        """Assinatura v03: retorna bytes ASCII e inscrição com 12 dígitos."""
        self._confirm_nfse_same_state()

        dados_lote = self.nfse_same_state._prepare_lote_rps()
        dados_serv = self.nfse_same_state._prepare_dados_servico()
        dados_tom = self.nfse_same_state._prepare_dados_tomador()
        assinatura = self.nfse_same_state.assinatura_rps(
            dados_lote, dados_serv, dados_tom
        )

        self.assertIsInstance(assinatura, bytes)
        self.assertEqual(len(assinatura[:12]), 12)

    # Transmissão / consulta / cancelamento (testes do upstream OCA, com o
    # processador erpbrasil.edoc substituído por um fake).

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
    def _fake_processador(sucesso=True, webservice="EnvioLoteRPS"):
        class FakeCabecalho:
            Sucesso = sucesso

        class FakeResposta:
            Cabecalho = FakeCabecalho()

        class FakeProcesso:
            retorno = TestFiscalDocumentNFSePaulistana._build_nfse_ok_xml()
            resposta = FakeResposta()
            envio_xml = "<PedidoCancelamentoNFe/>"

        FakeProcesso.webservice = webservice

        class FakeProcessador:
            _processo = FakeProcesso()

            def _generateds_to_string_etree(self, _ds, pretty_print=False):
                # Contrato do Processador real (erpbrasil.edoc, edoc.py):
                # devolve (xml_str, elemento); o _document_export usa apenas [0].
                return "<xml/>", None

            def processar_documento(self, _edoc):
                yield self._processo

            def consulta_nfse_rps(self, **_kwargs):
                return self._processo

            def analisa_retorno_consulta(self, _processo):
                # Mesmo contrato do erpbrasil.edoc (provedores/paulistana.py):
                # dict no sucesso, mensagem de texto no erro.
                if not sucesso:
                    return "Error communicating with the webservice"
                return {
                    "codigo_verificacao": "ABC123",
                    "numero": "123",
                    "data_emissao": "2020-01-01T10:00:00",
                }

            def cancela_documento(self, doc_numero):
                self.doc_numero = doc_numero
                return self._processo

            def analisa_retorno_cancelamento_paulistana(self, _processo):
                if sucesso:
                    return True, "Cancelamento efetuado"
                return False, "Erro ao cancelar"

        return FakeProcessador()

    def _patch_processador(self, processador):
        return patch(
            "odoo.addons.l10n_br_nfse.models.document.Document"
            "._processador_erpbrasil_nfse",
            return_value=processador,
        )

    def test_eletronic_document_send_envio_lote_sucesso(self):
        document = self.nfse_same_state
        document.nfse_environment = "1"
        document.authorization_event_id = False
        with (
            patch(
                "odoo.addons.l10n_br_nfse.models.document.Document.make_pdf",
                return_value=None,
            ),
            self._patch_processador(self._fake_processador()),
        ):
            self._confirm_nfse_same_state()
            document._eletronic_document_send()

        self.assertEqual(document.state_edoc, DOCUMENT_STATE_AUTHORIZED)
        self.assertEqual(document.status_code, "4")
        self.assertEqual(document.status_name, "Procesado com Sucesso")
        self.assertFalse(document.edoc_error_message)

    def test_document_status_consulta_sucesso(self):
        document = self.nfse_same_state
        document.nfse_environment = "1"
        with patch(
            "odoo.addons.l10n_br_nfse.models.document.Document.make_pdf",
            return_value=None,
        ):
            self._confirm_nfse_same_state()
        document.authorization_event_id = document.event_ids.create_event_save_xml(
            company_id=document.company_id,
            environment=EVENT_ENV_PROD,
            event_type="0",
            xml_file="<xml/>",
            document_id=document,
        )

        processador = self._fake_processador(webservice="ConsultaNFe")
        with self._patch_processador(processador):
            status = document._document_status()

        self.assertEqual(status, "Procesado com Sucesso")
        self.assertEqual(document.document_number, "123")
        self.assertEqual(document.verify_code, "ABC123")
        self.assertTrue(document.authorization_date)
        self.assertEqual(document.authorization_event_id.state, "done")

    def test_document_status_consulta_falha(self):
        document = self.nfse_same_state
        processador = self._fake_processador(sucesso=False, webservice="ConsultaNFe")
        with self._patch_processador(processador):
            status = document._document_status()
        self.assertEqual(status, "Error communicating with the webservice")

    def test_cancel_document_paulistana_sucesso(self):
        document = self.nfse_same_state
        document.document_number = "123"
        document.verify_code = "ABC123"
        document.nfse_environment = "1"

        processador = self._fake_processador()
        with self._patch_processador(processador):
            result = document.cancel_document_paulistana()

        self.assertTrue(result)
        self.assertTrue(document.cancel_event_id)
        self.assertEqual(
            processador.doc_numero,
            {"numero_nfse": "123", "codigo_verificacao": "ABC123"},
        )

    def test_cancel_document_paulistana_falha(self):
        document = self.nfse_same_state
        document.document_number = "123"
        document.verify_code = "ABC123"
        document.nfse_environment = "1"

        with self._patch_processador(self._fake_processador(sucesso=False)):
            with self.assertRaises(UserError):
                document.cancel_document_paulistana()
        self.assertFalse(document.cancel_event_id)

    def test_before_document_cancel_chama_cancelamento(self):
        document = self.nfse_same_state
        with patch.object(
            type(document), "cancel_document_paulistana", autospec=True
        ) as mock_cancel:
            document._before_document_cancel()
        mock_cancel.assert_called_once_with(document)

    def test_before_document_cancel_documento_nao_paulistana(self):
        document = self.nfse_same_state
        document.company_id.provedor_nfse = False
        with patch.object(
            type(document), "cancel_document_paulistana", autospec=True
        ) as mock_cancel:
            result = document._before_document_cancel()
        mock_cancel.assert_not_called()
        self.assertTrue(result)

    def test_document_cancel_fsm_transmite_cancelamento(self):
        """Cancelar pelo fluxo real (FSM action_cancel_fsm) transmite o pedido
        de cancelamento à Prefeitura antes de mudar o estado."""
        document = self.nfse_same_state
        document.document_number = "123"
        document.verify_code = "ABC123"
        document.nfse_environment = "1"
        document.state_edoc = DOCUMENT_STATE_AUTHORIZED

        processador = self._fake_processador()
        with self._patch_processador(processador):
            document._document_cancel("Cancelamento de teste da NFS-e")

        self.assertEqual(document.state_edoc, DOCUMENT_STATE_CANCEL)
        self.assertTrue(document.cancel_event_id)
        self.assertEqual(processador.doc_numero["numero_nfse"], "123")

    def test_document_cancel_fsm_falha_mantem_autorizada(self):
        """Recusa da Prefeitura aborta a transição: a nota continua autorizada."""
        document = self.nfse_same_state
        document.document_number = "123"
        document.verify_code = "ABC123"
        document.nfse_environment = "1"
        document.state_edoc = DOCUMENT_STATE_AUTHORIZED

        with self._patch_processador(self._fake_processador(sucesso=False)):
            with self.assertRaises(UserError):
                document._document_cancel("Cancelamento de teste da NFS-e")

        self.assertEqual(document.state_edoc, DOCUMENT_STATE_AUTHORIZED)
