# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

"""Base e fábricas de apoio aos testes do provedor Barueri.

Concentra aqui a montagem dos dublês do webservice (processador, processos e
arquivos de retorno), que de outro modo se repetiria em quase todos os testes.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from odoo.addons.l10n_br_fiscal.constants.fiscal import EVENT_ENV_PROD
from odoo.addons.l10n_br_nfse.tests.test_fiscal_document_nfse_common import (
    TestFiscalDocumentNFSeCommon,
)

MODULE = "odoo.addons.l10n_br_nfse_barueri.models.document"
BARUERI_CITY = "l10n_br_base.city_3505708"
OUTRA_CITY = "l10n_br_base.city_3132404"
VALS_SUCESSO = {"status_code": 1, "status_name": "Successfully Processed"}
VALS_ERRO = {"status_code": 2, "status_name": "Processed with Error"}


class TestBarueriCommon(TestFiscalDocumentNFSeCommon):
    def setUp(self):
        super().setUp()
        self.company.provedor_nfse = "barueri"

    def _documento(self, com_evento=False, **vals):
        """Documento Barueri com datas válidas e, opcionalmente, o evento de
        autorização que os fluxos de envio e consulta exigem."""
        document = self.nfse_same_state
        now = datetime.now()
        document.company_id.city_id = self.env.ref(BARUERI_CITY)
        document.document_type = "SE"
        document.write(dict({"document_date": now, "date_in_out": now}, **vals))
        document.authorization_event_id = False
        if com_evento:
            event = document.event_ids.create_event_save_xml(
                company_id=document.company_id,
                environment=EVENT_ENV_PROD,
                event_type="0",
                xml_file="<xml/>",
                document_id=document,
            )
            event.protocol_date = now
            document.authorization_event_id = event
        return document

    @staticmethod
    def _processador(**retornos):
        """Processador falso: cada argumento vira um método que ignora os
        parâmetros recebidos e devolve sempre o valor informado."""
        return SimpleNamespace(
            **{
                nome: (lambda v: lambda *a, **kw: v)(valor)
                for nome, valor in retornos.items()
            }
        )

    @staticmethod
    def _patch_processador(document, processador):
        return patch.object(
            type(document), "_processador_erpbrasil_nfse", return_value=processador
        )

    @staticmethod
    def _arquivo_retorno(status="A", numero="1", autenticidade="AUTH"):
        """Par (patch de parse_linha_exporta, conteúdo do arquivo) para um
        retorno de duas linhas, cujo registro tipo 2 é lido por posição."""
        campos = [SimpleNamespace(valor="") for _ in range(15)]
        for indice, valor in (
            (2, numero),
            (3, "20260101"),
            (4, "120000"),
            (5, autenticidade),
            (10, status),
            (14, "12345678000195"),
        ):
            campos[indice] = SimpleNamespace(valor=valor)
        linhas = {
            "linha0": SimpleNamespace(campos=[]),
            "linha1": SimpleNamespace(campos=campos),
        }
        patcher = patch(
            f"{MODULE}.parse_linha_exporta", side_effect=lambda linha: linhas[linha]
        )
        return patcher, "linha0\nlinha1".encode("latin1")

    def _processador_cancelamento(
        self, protocolo="PROTO", status=1, nome_arquivo="arq.txt", arquivo=None
    ):
        """Processador que percorre o fluxo de cancelamento Barueri."""
        lista = SimpleNamespace(NomeArqRetorno=nome_arquivo) if nome_arquivo else None
        return self._processador(
            envia_documento=SimpleNamespace(
                resposta=SimpleNamespace(ProtocoloRemessa=protocolo),
                envio_xml="<xml/>",
            ),
            consulta_nfse_rps=SimpleNamespace(
                resposta=SimpleNamespace(ListaNfeArquivosRPS=lista)
            ),
            analisa_retorno_consulta=(status, "mensagem"),
            baixar_lote_rps=SimpleNamespace(
                retorno=SimpleNamespace(ArquivoRPSBase64=arquivo) if arquivo else None
            ),
        )

    @staticmethod
    def _capture_registros(document, cancel=False, exportar=b"LINHA"):
        """Serializa o lote capturando os registros entregues ao RPS, o que
        permite inspecioná-los um a um em vez do arquivo exportado."""
        captured = {}

        class FakeRPS:
            def __init__(self, registros):
                captured["registros"] = registros

            def exportar(self):
                return exportar

        with patch(f"{MODULE}.RPS", FakeRPS):
            resultado = document._serialize_barueri_lote_rps(cancel=cancel)
        return captured["registros"], resultado

    @staticmethod
    def _patch_dados(document, servico=None, tomador=None):
        """Substitui os dados de serviço e de tomador por valores controlados."""
        dados_servico = dict(
            {
                "codigo_tributacao_municipio": "1401",
                "valor_servicos": 100.0,
                "discriminacao": "Serviço de manutenção",
                "codigo_nbs": "1.2301",
            },
            **(servico or {}),
        )
        dados_tomador = dict(
            {
                "cnpj": "12345678000195",
                "razao_social": "Tomador Ação Ltda",
                "endereco": "Rua São João",
                "numero": "100",
                "complemento": "Sala 2",
                "bairro": "Centro",
                "municipio": "Barueri",
                "uf": "SP",
                "cep": "06.401-000",
                "email": "tomador@example.com",
            },
            **(tomador or {}),
        )
        return patch.object(
            type(document),
            "_serialize_barueri_dados_servico",
            return_value=dados_servico,
        ), patch.object(
            type(document),
            "_serialize_barueri_dados_tomador",
            return_value=dados_tomador,
        )
