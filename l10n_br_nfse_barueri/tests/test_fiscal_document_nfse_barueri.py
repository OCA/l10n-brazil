# Copyright 2020 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import os
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from nfselib.barueri.NFeLoteEnviarArquivo import NFeLoteEnviarArquivo
from xmldiff import main

from odoo.tools import config

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    PROCESSADOR_NENHUM,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_REJEITADA,
)
from odoo.addons.l10n_br_nfse_barueri.models.document import (
    filter_barueri,
    filter_oca_nfse,
    parse_linha_exporta,
)

from ... import l10n_br_nfse_barueri
from .common import (
    MODULE,
    OUTRA_CITY,
    VALS_ERRO,
    VALS_SUCESSO,
    TestBarueriCommon,
)

_logger = logging.getLogger(__name__)


class TestFiscalDocumentNFSeBarueri(TestBarueriCommon):
    # --- XML esperado, campos calculados e ações -----------------------------

    def test_nfse_barueri_xml_esperado(self):
        """O XML gerado para Barueri deve permanecer compatível com o esperado."""
        xml_path = os.path.join(
            l10n_br_nfse_barueri.__path__[0], "tests", "nfse", "nfse.xml"
        )
        self.nfse_same_state.rps_number = "50"
        self.nfse_same_state.document_number = "50"

        with patch(
            "odoo.addons.l10n_br_nfse.models.document.Document.make_pdf",
            return_value=None,
        ):
            self.nfse_same_state.action_document_confirm()
            emissao = datetime.strptime("2020-06-04T11:58:46", "%Y-%m-%dT%H:%M:%S")
            self.nfse_same_state.document_date = emissao
            self.nfse_same_state.date_in_out = emissao
            self.nfse_same_state.with_context(lang="pt_BR")._document_export()

        output = os.path.join(
            config["data_dir"],
            "filestore",
            self.cr.dbname,
            self.nfse_same_state.send_file_id.store_fname,
        )
        diff = main.diff_files(xml_path, output)
        _logger.info("Diff with expected XML (if any): %s", diff)
        # Espera-se no máximo pequenas diferenças irrelevantes.
        self.assertLessEqual(len(diff), 1)

    def test_is_nfse_barueri_flag(self):
        """O campo técnico exige documento de serviço e empresa em Barueri."""
        document = self._documento()
        self.assertTrue(document.is_nfse_barueri)

        document.company_id.city_id = self.env.ref(OUTRA_CITY)
        document.invalidate_cache(fnames=["is_nfse_barueri"])
        self.assertFalse(document.is_nfse_barueri)

    def test_compute_url_nfse_barueri(self):
        """A URL varia por ambiente e fica vazia sem os dados obrigatórios ou
        quando o documento não é de Barueri."""
        document = self._documento()
        document.partner_id.cnpj_cpf = "12.345.678/0001-95"
        document.verify_code = "ABC123"
        sufixo = (
            "/nfe/wfimagemNota.aspx" "?CODIGOAUTENTICIDADE=ABC123&NUMDOC=12345678000195"
        )
        for ambiente, base in (
            ("1", "https://www.barueri.sp.gov.br"),
            ("2", "https://testeeiss.barueri.sp.gov.br"),
        ):
            with self.subTest(ambiente=ambiente):
                document.nfse_environment = ambiente
                document._compute_url_nfse_barueri()
                self.assertEqual(document.url_nfse_barueri, base + sufixo)

        document.verify_code = False
        document.partner_id.cnpj_cpf = False
        document._compute_url_nfse_barueri()
        self.assertEqual(document.url_nfse_barueri, "")

        document.verify_code = "ABC123"
        document.company_id.city_id = self.env.ref(OUTRA_CITY)
        document._compute_url_nfse_barueri()
        self.assertEqual(document.url_nfse_barueri, "")

    def test_action_open_nfse_barueri(self):
        """A ação abre a URL da NFSe e a fatura delega para o documento."""
        document = self._documento()
        action = document.action_open_nfse_barueri()

        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertEqual(action["url"], document.url_nfse_barueri)
        self.assertEqual(action["target"], "new")

        move = self.env["account.move"].new({"fiscal_document_id": document.id})
        with patch.object(
            type(document), "action_open_nfse_barueri", return_value="ACTION"
        ) as mock_action:
            self.assertEqual(move.action_open_nfse_barueri(), "ACTION")
        mock_action.assert_called_once()

    # --- Funções de módulo ---------------------------------------------------

    def test_filter_oca_nfse_e_filter_barueri(self):
        """Os filtros restringem os hooks a NFSe processada via OCA em Barueri."""
        document = self.nfse_same_state
        self.assertTrue(filter_oca_nfse(document))
        self.assertTrue(filter_barueri(document))

        document.company_id.processador_edoc = PROCESSADOR_NENHUM
        self.assertFalse(filter_oca_nfse(document))
        document.company_id.processador_edoc = PROCESSADOR_OCA

        document.company_id.provedor_nfse = False
        self.assertFalse(filter_barueri(document))

    def test_parse_linha_exporta_despacha_por_tipo(self):
        """Cada tipo é roteado para a sua classe; tipo desconhecido é erro."""
        nomes = ("Tipo1", "Tipo2", "Tipo3", "Tipo4", "Tipo9")
        with patch.multiple(
            MODULE,
            **{
                f"NFSeRegistro{n}": MagicMock(from_line=MagicMock(return_value=n))
                for n in nomes
            },
        ):
            for tipo, esperado in zip("12349", nomes, strict=True):
                with self.subTest(tipo=tipo):
                    self.assertEqual(parse_linha_exporta(f"{tipo}resto"), esperado)
            # O tipo "5" também é tratado pela classe do tipo 4.
            self.assertEqual(parse_linha_exporta("5resto"), "Tipo4")

        with self.assertRaises(ValueError):
            parse_linha_exporta("Xresto")

    def test_sem_acento(self):
        """A normalização remove acentuação e tolera valores vazios."""
        self.assertEqual(self.nfse_same_state._sem_acento("São Paulo Ç"), "Sao Paulo C")
        self.assertEqual(self.nfse_same_state._sem_acento(None), "")

    # --- Serialização do arquivo RPS -----------------------------------------

    def test_serialize_barueri_lote_rps_emissao(self):
        """Na emissão o tipo 2 usa a data do documento e situação "E"; o
        arquivo exportado é convertido para bytes e outro tipo é erro."""
        document = self._documento(
            document_date=datetime(2026, 3, 10, 14, 5, 30),
            date_in_out=datetime(2026, 3, 10, 14, 5, 30),
            rps_number="77",
        )
        registros, resultado = self._capture_registros(document, exportar="LINHA")
        registro_tipo2 = registros[1]

        self.assertEqual(resultado, b"LINHA")
        self.assertEqual(registro_tipo2.SituacaoRPS, "E")
        self.assertEqual(registro_tipo2.NumeroRPS, "0000000077")
        self.assertEqual(registro_tipo2.DataRPS, "20260310")
        self.assertEqual(registro_tipo2.HoraRPS, "140530")
        self.assertEqual(registro_tipo2.CodigoMotivoCancelamento, "")
        self.assertEqual(registro_tipo2.NumeroNFeCancelada, "")
        self.assertEqual(registro_tipo2.DescricaoCancelamento, "")

        with self.assertRaises(ValueError):
            self._capture_registros(document, exportar=None)

    def test_serialize_barueri_lote_rps_cancelamento(self):
        """No cancelamento o tipo 2 usa situação "C", RPS zerado e referencia
        a NFe cancelada, com a descrição normalizada e truncada."""
        document = self._documento(
            document_number="123",
            authorization_date=datetime(2026, 1, 15, 10, 30, 0),
            cancel_reason="Serviço não prestado à São Paulo",
        )
        registros, _resultado = self._capture_registros(document, cancel=True)
        registro_tipo2 = registros[1]

        self.assertEqual(registro_tipo2.SituacaoRPS, "C")
        self.assertEqual(registro_tipo2.NumeroRPS, "0" * 10)
        self.assertEqual(registro_tipo2.CodigoMotivoCancelamento, "01")
        self.assertEqual(registro_tipo2.NumeroNFeCancelada, "0000123")
        self.assertEqual(registro_tipo2.SerieNFeCancelada, "")
        self.assertEqual(registro_tipo2.DataEmissaoNFeCancelada, "20260115")
        self.assertEqual(
            registro_tipo2.DescricaoCancelamento, "Servico nao prestado a Sao Paulo"
        )
        # O cancelamento usa a data corrente, não a de emissão do documento.
        self.assertEqual(registro_tipo2.DataRPS, datetime.now().strftime("%Y%m%d"))

    def test_serialize_barueri_lote_rps_retencoes_e_rodape(self):
        """Cada retenção gera um registro tipo 3 e o rodapé tipo 9 soma as
        linhas, o valor dos serviços e o das retenções."""
        document = self._documento()
        p_servico, p_tomador = self._patch_dados(
            document,
            servico={
                "valor_ir_retido": 1.5,
                "valor_pis_retido": 0.65,
                "valor_cofins_retido": 3.0,
                "valor_csll_retido": 1.0,
            },
        )
        with p_servico, p_tomador:
            registros, _resultado = self._capture_registros(document)

        registros_tipo3 = [r for r in registros if r.TipoRegistro == 3]
        self.assertEqual(
            [r.CodigoOutrosValores for r in registros_tipo3], ["01", "02", "03", "04"]
        )
        self.assertEqual(registros_tipo3[0].Valor, str(150).zfill(15))
        self.assertEqual(registros_tipo3[1].Valor, str(65).zfill(15))

        registro_tipo2, registro_tipo9 = registros[1], registros[-1]
        self.assertEqual(registro_tipo2.ValorTotalRetencoes, str(615).zfill(15))
        # tipo 1 + tipo 2 + 4x tipo 3 + tipo 4 + tipo 5 = 8, mais o rodapé.
        self.assertEqual(registro_tipo9.NumeroTotalLinhas, str(9).zfill(7))
        self.assertEqual(registro_tipo9.ValorTotalValores, str(615).zfill(15))
        self.assertEqual(
            int(registro_tipo9.ValorTotalServicos),
            int(registro_tipo2.QuantidadeServico) * int(registro_tipo2.ValorServico),
        )
        # O valor unitário é o total do serviço rateado pela quantidade.
        self.assertEqual(
            int(registro_tipo2.ValorServico),
            round(100.0 / int(registro_tipo2.QuantidadeServico) * 100),
        )

    def test_serialize_barueri_lote_rps_dados_do_tomador(self):
        """Sem retenções não há tipo 3; os dados do tomador são normalizados,
        o CEP higienizado e o indicador segue o tipo de documento."""
        document = self._documento()
        p_servico, p_tomador = self._patch_dados(document)
        with p_servico, p_tomador:
            registros, _resultado = self._capture_registros(document)

        registro_tipo2, registro_tipo9 = registros[1], registros[-1]
        self.assertFalse([r for r in registros if r.TipoRegistro == 3])
        self.assertEqual(registro_tipo9.NumeroTotalLinhas, str(5).zfill(7))
        self.assertEqual(registro_tipo9.ValorTotalValores, str(0).zfill(15))
        self.assertEqual(registro_tipo2.RazaoSocialNomeTomador, "Tomador Acao Ltda")
        self.assertEqual(registro_tipo2.EnderecoLogradouroTomador, "Rua Sao Joao")
        self.assertEqual(registro_tipo2.CEPLogradouroTomador, "06401000")

        casos = (
            ({}, "2", "12345678000195"),
            ({"cnpj": "", "cpf": "12345678901"}, "1", "00012345678901"),
            # Sem documento, CEP e número, caem nos padrões do layout.
            ({"cnpj": "", "cpf": "", "cep": "", "numero": ""}, "1", "0" * 14),
        )
        for tomador, indicador, documento_esperado in casos:
            with self.subTest(tomador=tomador):
                p_servico, p_tomador = self._patch_dados(document, tomador=tomador)
                with p_servico, p_tomador:
                    registros, _resultado = self._capture_registros(document)

                self.assertEqual(registros[1].IndicadorCPFCNPJTomador, indicador)
                self.assertEqual(registros[1].CPFCNPJTomador, documento_esperado)

        self.assertEqual(registros[1].CEPLogradouroTomador, "")
        self.assertEqual(registros[1].NumeroLogradouroTomador, "10")

    def test_serialize_nfse_barueri_monta_lote(self):
        """serialize_nfse_barueri devolve o lote com o RPS em bytes."""
        lote = self._documento().serialize_nfse_barueri()

        self.assertIsInstance(lote, NFeLoteEnviarArquivo)
        self.assertIn(".txt", lote.NomeArquivoRPS)
        self.assertIsInstance(lote.ArquivoRPSBase64, (bytes, bytearray))

    def test_serialize_anexa_lote_apenas_quando_barueri(self):
        """O hook _serialize só anexa o lote Barueri para o provedor correto."""
        document = self.nfse_same_state

        with patch.object(
            type(document), "serialize_nfse_barueri", return_value="LOTE_FAKE"
        ) as mock_serialize:
            self.assertIn("LOTE_FAKE", document._serialize([]))
        mock_serialize.assert_called_once()

        document.company_id.provedor_nfse = False
        with patch.object(
            type(document), "serialize_nfse_barueri", return_value="LOTE_FAKE"
        ) as mock_serialize:
            self.assertNotIn("LOTE_FAKE", document._serialize([]))
        mock_serialize.assert_not_called()

    # --- Comunicação com o webservice ----------------------------------------

    def test_baixar_xml_nfse_monta_url_corretamente(self):
        """O download do XML monta a URL esperada e valida a resposta."""
        with patch(f"{MODULE}.requests.get") as mock_get:
            mock_get.return_value = MagicMock(text="<xml/>")
            result = self.nfse_same_state._baixar_xml_nfse("ABC123", "12345678000195")

        called_url = mock_get.call_args[0][0]
        self.assertIn("codigoautenticidade=ABC123", called_url)
        self.assertIn("numdoc=12345678000195", called_url)
        mock_get.return_value.raise_for_status.assert_called_once()
        self.assertEqual(result, "<xml/>")

    def test_get_protocolo_envio_consulta_e_situacao(self):
        """Fluxo feliz: envio do lote, consulta do protocolo e situação."""
        document = self._documento(com_evento=True)

        def _processo(webservice, protocolo=None, lista=None):
            return SimpleNamespace(
                webservice=webservice,
                resposta=SimpleNamespace(
                    ProtocoloRemessa=protocolo,
                    ListaMensagemRetorno=None,
                    ListaNfeArquivosRPS=lista,
                ),
            )

        processador = self._processador(
            processar_documento=iter(
                [
                    _processo("NFeLoteEnviarArquivo", protocolo="PROTO-ENVIO"),
                    _processo("NFeLoteBaixarArquivo", protocolo="PROTO-CONSULTA"),
                    _processo(
                        "NFeLoteStatusArquivo",
                        lista=SimpleNamespace(
                            SituacaoArq="1", NomeArqRetorno="arquivo.txt"
                        ),
                    ),
                ]
            )
        )

        with patch.object(type(document), "serialize", return_value=["EDOC"]):
            vals, protocolo = document._get_protocolo(document, processador, {})

        self.assertEqual(protocolo, "PROTO-CONSULTA")
        self.assertEqual(vals, {"status_code": 1, "return_filename": "arquivo.txt"})
        self.assertEqual(
            document.authorization_event_id.lot_receipt_number, "PROTO-ENVIO"
        )

    def test_get_protocolo_rejeitado_monta_mensagem_de_erro(self):
        """Consulta sem protocolo monta a mensagem de erro e rejeita o documento."""
        document = self.nfse_same_state
        processador = self._processador(
            processar_documento=iter(
                [
                    SimpleNamespace(
                        webservice="NFeLoteBaixarArquivo",
                        resposta=SimpleNamespace(
                            ProtocoloRemessa=None,
                            ListaNfeArquivosRPS=None,
                            ListaMensagemRetorno=SimpleNamespace(
                                MensagemRetorno=[
                                    SimpleNamespace(
                                        Codigo="101",
                                        Mensagem="Erro um",
                                        Correcao="Corrija A",
                                    ),
                                    SimpleNamespace(
                                        Codigo="102",
                                        Mensagem="Erro dois",
                                        Correcao=None,
                                    ),
                                ]
                            ),
                        ),
                    )
                ]
            )
        )

        with patch.object(
            type(document), "serialize", return_value=["EDOC"]
        ), patch.object(type(document), "_change_state") as mock_change_state:
            vals, protocolo = document._get_protocolo(document, processador, {})

        self.assertIsNone(protocolo)
        self.assertEqual(vals["status_code"], 3)
        self.assertIn("101 - Erro um - Correção: Corrija A", vals["edoc_error_message"])
        self.assertIn("102 - Erro dois - Correção: \n", vals["edoc_error_message"])
        mock_change_state.assert_called_once_with(SITUACAO_EDOC_REJEITADA)

    # --- Leitura do retorno do lote ------------------------------------------

    def test_set_response_sem_resposta_nao_altera_vals(self):
        """Processo sem resposta devolve vals inalterado."""
        document = self.nfse_same_state
        processador = self._processador(
            baixar_lote_rps=SimpleNamespace(resposta=None, retorno=None)
        )

        vals = document._set_response(
            document, processador, "PROTOCOLO", dict(VALS_SUCESSO)
        )

        self.assertEqual(vals, VALS_SUCESSO)

    def test_set_response_ramos_de_erro(self):
        """Com status 2, a mensagem vem do webservice (Codigo != OK200) ou dos
        códigos extraídos do próprio arquivo de retorno."""
        document = self.nfse_same_state
        casos = (
            (
                SimpleNamespace(
                    Codigo="999", Mensagem="Falha geral", Correcao="Revisar cadastro"
                ),
                None,
                ["999 - Falha geral - Correção: Revisar cadastro"],
            ),
            (
                SimpleNamespace(Codigo="OK200", Mensagem="", Correcao=""),
                b"xxx000;yyy102;fim",
                [
                    "000 - Layout Inválido",
                    "102 - inválida ou já informada em outro arquivo de remessa",
                ],
            ),
        )
        for mensagens, conteudo, esperados in casos:
            with self.subTest(codigo=mensagens.Codigo):
                processador = self._processador(
                    baixar_lote_rps=SimpleNamespace(
                        resposta=SimpleNamespace(ListaMensagemRetorno=mensagens),
                        retorno=SimpleNamespace(ArquivoRPSBase64=conteudo),
                    )
                )
                with patch.object(type(document), "_change_state") as mock_change_state:
                    vals = document._set_response(
                        document, processador, "PROTOCOLO", dict(VALS_ERRO)
                    )

                for esperado in esperados:
                    self.assertIn(esperado, vals["edoc_error_message"])
                self.assertEqual(
                    document.edoc_error_message, vals["edoc_error_message"]
                )
                mock_change_state.assert_called_once_with(SITUACAO_EDOC_REJEITADA)

    def test_set_response_sucesso_autorizada(self):
        """Status "A" grava os dados da NFSe e autoriza o documento."""
        document = self._documento(com_evento=True)
        patch_parse, arquivo = self._arquivo_retorno(
            status="A", numero="1234", autenticidade="AUTH123"
        )
        processador = self._processador(
            baixar_lote_rps=SimpleNamespace(
                resposta=True, retorno=SimpleNamespace(ArquivoRPSBase64=arquivo)
            )
        )

        with patch_parse, patch.object(
            type(document), "_baixar_xml_nfse", return_value="<xml/>"
        ), patch.object(type(document), "_change_state") as mock_change_state, patch(
            "odoo.addons.l10n_br_nfse.models.document.Document.make_pdf",
            return_value=None,
        ):
            vals = document._set_response(
                document, processador, "PROTOCOLO", dict(VALS_SUCESSO)
            )

        self.assertEqual(document.document_number, "1234")
        self.assertEqual(document.verify_code, "AUTH123")
        self.assertEqual(vals["authorization_date"], datetime(2026, 1, 1, 12, 0, 0))
        mock_change_state.assert_called_once_with(SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(document.authorization_event_id.status_code, "1")

    def test_set_response_sucesso_cancelada(self):
        """Status "C" cria o evento de cancelamento e cancela o documento."""
        document = self.nfse_same_state
        patch_parse, arquivo = self._arquivo_retorno(status="C")
        processador = self._processador(
            baixar_lote_rps=SimpleNamespace(
                resposta=True, retorno=SimpleNamespace(ArquivoRPSBase64=arquivo)
            )
        )

        with patch_parse, patch.object(
            type(document), "_baixar_xml_nfse", return_value="<xml/>"
        ), patch.object(type(document), "_change_state") as mock_change_state:
            document._set_response(
                document, processador, "PROTOCOLO", dict(VALS_SUCESSO)
            )

        self.assertEqual(document.state_edoc, SITUACAO_EDOC_CANCELADA)
        self.assertEqual(document.cancel_event_id.status_code, "2")
        mock_change_state.assert_not_called()

    # --- Consulta de status e envio ------------------------------------------

    def test_document_status_delega_para_set_response(self):
        """Com status pendente, as situações 1 e 2 delegam para _set_response;
        um status já definitivo não reprocessa o retorno."""
        for status, status_code, arquivo, mensagem in (
            (1, "-1", "arq.txt", "NFSe processada"),
            (2, "-2", "arq-erro.txt", "NFSe rejeitada"),
            (1, "1", None, "NFSe processada"),
        ):
            with self.subTest(status_code=status_code):
                document = self._documento(com_evento=True, status_code=status_code)
                lista = SimpleNamespace(NomeArqRetorno=arquivo) if arquivo else None
                processador = self._processador(
                    consulta_nfse_rps=SimpleNamespace(
                        resposta=SimpleNamespace(ListaNfeArquivosRPS=lista)
                    ),
                    analisa_retorno_consulta=(status, mensagem),
                )

                with self._patch_processador(document, processador), patch.object(
                    type(document), "_set_response", return_value={}
                ) as mock_set_response:
                    self.assertEqual(document._document_status(), mensagem)

                if arquivo is None:
                    mock_set_response.assert_not_called()
                    continue
                called_vals = mock_set_response.call_args[0][3]
                self.assertEqual(called_vals["status_code"], status)
                self.assertEqual(called_vals["return_filename"], arquivo)

    def test_eletronic_document_send_lote_pendente(self):
        """Os status -1 e -2 marcam o lote como ainda não processado."""
        document = self._documento()

        for status_code in (-1, -2):
            with self.subTest(status_code=status_code):
                with self._patch_processador(document, SimpleNamespace()), patch.object(
                    type(document),
                    "_get_protocolo",
                    return_value=({"status_code": status_code}, None),
                ), patch.object(type(document), "_change_state") as mock_change_state:
                    document._eletronic_document_send()

                self.assertEqual(document.status_name, "Batch not yet processed")
                mock_change_state.assert_called_once_with(SITUACAO_EDOC_ENVIADA)

    def test_eletronic_document_send_protocolo_existente_e_validado(self):
        """Com protocolo de autorização já gravado, o status vai para "Validated"."""
        document = self._documento(com_evento=True)
        document.authorization_event_id.protocol_number = "PROTO-EXISTENTE"

        with self._patch_processador(document, SimpleNamespace()), patch.object(
            type(document), "_get_protocolo"
        ) as mock_get_protocolo:
            document._eletronic_document_send()

        mock_get_protocolo.assert_not_called()
        self.assertEqual(document.status_name, "Validated")

    def test_eletronic_document_send_delega_para_set_response(self):
        """Os status 1 e 2 delegam para _set_response; "return_filename" não é
        campo do modelo e precisa ser descartado antes do write."""
        document = self._documento()
        casos = (
            (1, "Successfully Processed", {"authorization_protocol": "PROTO"}),
            (2, "Processed with Error", {}),
        )
        for status_code, status_name, extra in casos:
            with self.subTest(status_code=status_code):
                resposta = dict(
                    {
                        "status_code": status_code,
                        "status_name": status_name,
                        "return_filename": "arq.txt",
                    },
                    **extra,
                )
                with self._patch_processador(document, SimpleNamespace()), patch.object(
                    type(document),
                    "_get_protocolo",
                    return_value=({"status_code": status_code}, "PROTO"),
                ), patch.object(
                    type(document), "_set_response", return_value=resposta
                ) as mock_set_response:
                    document._eletronic_document_send()

                args = mock_set_response.call_args[0]
                self.assertEqual(args[2], "PROTO")
                self.assertEqual(args[3]["status_name"], status_name)
                self.assertEqual(document.status_name, status_name)

    # --- Cancelamento --------------------------------------------------------

    def test_cancel_document_barueri_ramos_de_aborto(self):
        """Cada pré-condição não satisfeita aborta o cancelamento com False."""
        _patcher, arquivo_nao_cancelado = self._arquivo_retorno(status="E")
        casos = (
            ("sem protocolo de remessa", {"protocolo": None}),
            ("situação de consulta zerada", {"status": 0}),
            ("sem nome de arquivo de retorno", {"nome_arquivo": None}),
            ("baixa do lote sem conteúdo", {"arquivo": None}),
            ("registro de retorno não cancelado", {"arquivo": arquivo_nao_cancelado}),
        )
        for descricao, kwargs in casos:
            with self.subTest(descricao):
                document = self._documento(
                    com_evento=True, rps_number="1", rps_type="1"
                )
                patch_parse, _arquivo = self._arquivo_retorno(status="E")
                with patch_parse, self._patch_processador(
                    document, self._processador_cancelamento(**kwargs)
                ):
                    self.assertFalse(document._cancel_document_barueri())

    def test_cancel_document_barueri_lote_pendente(self):
        """Situação -1/-2 marca o cancelamento como pendente e aborta."""
        document = self._documento(com_evento=True, rps_number="1", rps_type="1")

        with self._patch_processador(
            document, self._processador_cancelamento(status=-1)
        ), patch.object(type(document), "_change_state") as mock_change_state:
            self.assertFalse(document._cancel_document_barueri())

        self.assertEqual(document.status_code, "-2")
        self.assertEqual(document.status_name, "Cancel batch not yet processed")
        mock_change_state.assert_called_once_with(SITUACAO_EDOC_ENVIADA)

    def test_cancel_document_barueri_sucesso(self):
        """Fluxo completo: gera o evento de cancelamento e cancela o documento."""
        document = self._documento(com_evento=True, rps_number="1", rps_type="1")
        patch_parse, arquivo = self._arquivo_retorno(status="C")

        with patch_parse, self._patch_processador(
            document, self._processador_cancelamento(arquivo=arquivo)
        ):
            self.assertTrue(document._cancel_document_barueri())

        self.assertEqual(document.state_edoc, SITUACAO_EDOC_CANCELADA)
        self.assertTrue(document.cancel_event_id)

    def test_before_document_cancel(self):
        """O hook só delega para o cancelamento Barueri quando o filtro casa."""
        document = self.nfse_same_state

        with patch.object(
            type(document), "_cancel_document_barueri", return_value=True
        ) as mock_cancel:
            self.assertTrue(document._before_document_cancel())
        mock_cancel.assert_called_once()

        document.company_id.provedor_nfse = False
        with patch.object(type(document), "_cancel_document_barueri") as mock_cancel:
            self.assertTrue(document._before_document_cancel())
        mock_cancel.assert_not_called()

    def test_cron_document_status_barueri(self):
        """O cron consulta o status apenas quando há documentos enviados."""
        document = self.nfse_same_state
        model = self.env["l10n_br_fiscal.document"]

        for encontrados, chamado in ((document, True), (model, False)):
            with self.subTest(chamado=chamado):
                with patch.object(
                    type(document), "search", return_value=encontrados
                ), patch.object(type(document), "_document_status") as mock_status:
                    model._cron_document_status_barueri()

                self.assertEqual(mock_status.called, chamado)
