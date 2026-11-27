# Copyright 2023 - KMEE INFORMATICA LTDA
# Copyright 2026 Pop Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import copy
import logging
import time
from datetime import datetime
from urllib.parse import urlencode, urljoin

import pytz
from erpbrasil.base import misc
from nfselib.barueri.rps import (
    RegistroTipo1,
    RegistroTipo2,
    RegistroTipo3,
    RegistroTipo9,
)

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFSE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_REJEITADA,
)

from .rps_pmb004 import RegistroTipo4, RegistroTipo5

_logger = logging.getLogger(__name__)

# Namespace / endpoint / versão do layout atual exigido por Barueri (2026).
BARUERI_NS = "http://www.barueri.sp.gov.br/nfe"
BARUERI_WSRPS_ENDPOINT = "nfeservice/wsrps.asmx?WSDL"
# Imagem (PDF) da NFS-e no portal da Prefeitura, por ambiente.
BARUERI_URL_NFSE = {
    "1": "https://www.barueri.sp.gov.br/nfe/wfimagemNota.aspx",
    "2": "https://testeeiss.barueri.sp.gov.br/nfe/wfimagemNota.aspx",
}
BARUERI_LAYOUT_VERSION = "PMB004"
# Polling do processamento assíncrono do lote.
BARUERI_POLL_TRIES = 8
BARUERI_POLL_WAIT = 6
# Registro tipo 3: "Codigo de Outros Valores" de cada retencao federal. O
# leiaute nao tem codigo para o ISS retido, que Barueri apura sozinha.
BARUERI_RETENCOES = (
    ("01", "valor_ir_retido"),
    ("02", "valor_pis_retido"),
    ("03", "valor_cofins_retido"),
    ("04", "valor_csll_retido"),
    ("05", "valor_inss_retido"),
)
# Registro tipo 5, compra governamental: 1 = fornecimento com pagamento
# posterior.
BARUERI_OPERACAO_ENTE_GOVERNAMENTAL = "1"


def filter_oca_nfse(record):
    if record.processador_edoc == PROCESSADOR_OCA and record.document_type_id.code in [
        MODELO_FISCAL_NFSE,
    ]:
        return True
    return False


def filter_barueri(record):
    if record.company_id.provedor_nfse == "barueri":
        return True
    return False


def _new_registro(registro_cls):
    """Instancia um registro do nfselib com campos PROPRIOS.

    No nfselib.barueri 1.0.0 ``campos`` e um atributo de CLASSE: todas as
    instancias de RegistroTipo2 compartilham os mesmos CampoPosicional, entao o
    valor gravado para um documento (tomador, complemento, regime do Simples...)
    vaza para o proximo documento serializado no mesmo processo. A 1.1.0 cria os
    campos no ``__init__`` e zera ``campos`` na base: um registro declarado so
    com ``campos`` de classe (o nosso RegistroTipo4) sairia vazio. Copiamos a
    lista da classe quando a instancia nao tem campos proprios, o que funciona
    com as duas versoes.
    """
    registro = registro_cls()
    if not vars(registro).get("campos"):
        registro.campos = copy.deepcopy(type(registro).campos)
    return registro


def _blank_none(registro):
    """nfselib exporta ``str(None)`` == 'None' para campos não preenchidos.
    Trocamos None por '' para que o campo saia em branco/zeros conforme o tipo."""
    for campo in registro.campos:
        if campo.valor is None:
            campo.valor = ""
    return registro


def _rec(registro):
    r"""Exporta um registro e remove o terminador truncado.
    O nfselib define CaracterFimLinha com tamanho 1, truncando '\r\n' para '\r';
    removemos aqui para reconstruir com CRLF correto ao unir as linhas."""
    return _blank_none(registro).exportar().rstrip("\r\n")


def _decode_retorno(conteudo):
    """O retorno de Barueri vem em UTF-8 (a discriminacao do registro 3 traz
    acentos), embora o arquivo enviado seja ISO-8859-1."""
    try:
        return conteudo.decode("utf-8")
    except UnicodeDecodeError:
        return conteudo.decode("latin-1", errors="replace")


def _cents(value):
    """Valor monetário -> inteiro em centavos, sem separador decimal.
    Campos NUM do layout são zero-preenchidos à esquerda pelo exportador."""
    try:
        return str(int(round(float(value or 0) * 100)))
    except (TypeError, ValueError):
        return "0"


def _barueri_parse_mensagens(resposta):
    """Concatena as MensagemRetorno (Codigo - Mensagem - Correção) da resposta."""
    lista = getattr(resposta, "ListaMensagemRetorno", None)
    if not lista:
        return ""
    mensagens = getattr(lista, "MensagemRetorno", None)
    if mensagens is None and getattr(lista, "Codigo", None) is not None:
        mensagens = [lista]
    partes = []
    for mr in mensagens or []:
        correcao = getattr(mr, "Correcao", None)
        partes.append(
            "{} - {}{}".format(
                getattr(mr, "Codigo", "") or "",
                getattr(mr, "Mensagem", "") or "",
                f" - Correção: {correcao}" if correcao else "",
            )
        )
    return "\n".join(partes)


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    url_nfse_barueri = fields.Char(
        string="URL da NFS-e (Barueri)",
        compute="_compute_url_nfse_barueri",
    )

    @api.depends("verify_code", "partner_id.vat", "nfse_environment")
    def _compute_url_nfse_barueri(self):
        for doc in self:
            codigo = (doc.verify_code or "").strip()
            documento = misc.punctuation_rm(doc.partner_id.vat or "")
            base_url = BARUERI_URL_NFSE.get(doc.nfse_environment)
            if not (filter_barueri(doc) and codigo and documento and base_url):
                doc.url_nfse_barueri = False
                continue
            doc.url_nfse_barueri = "{}?{}".format(
                base_url,
                urlencode({"CODIGOAUTENTICIDADE": codigo, "NUMDOC": documento}),
            )

    def action_open_nfse_barueri(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": self.url_nfse_barueri,
            "target": "new",
        }

    @api.model
    def _cron_document_status_barueri(self):
        """Reconsulta os lotes de Barueri que ficaram em processamento."""
        documents = self.search(
            [
                ("state_edoc", "=", SITUACAO_EDOC_ENVIADA),
                ("company_id.provedor_nfse", "=", "barueri"),
            ],
            limit=25,
        ).filtered(filter_oca_nfse)
        for document in documents:
            document._document_status()

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_oca_nfse).filtered(filter_barueri):
            edocs.append(record.serialize_nfse_barueri())
        return edocs

    def _serialize_barueri_dados_servico(self):
        self.fiscal_line_ids.ensure_one()
        return self._prepare_dados_servico()

    def _serialize_barueri_dados_tomador(self):
        return self._prepare_dados_tomador()

    # ------------------------------------------------------------------
    # Serialização do arquivo TXT de RPS (layout PMB004)
    # ------------------------------------------------------------------
    def _barueri_build_registro_tipo4(self, dados, dados_servico, dados_tomador):
        """Registro Tipo 4 (ADN / IBS-CBS) — obrigatório no PMB004.
        Os códigos de IBS/CBS/NBS/indOp vêm do modelo fiscal do Odoo 18
        (l10n_br_fiscal), que já possui esses campos; precisam estar
        configurados conforme as tabelas de correlação (Anexos VII/VIII 2026)."""
        t4 = _new_registro(RegistroTipo4)
        # 1=Não optante, 2=MEI, 3=ME/EPP.  optante_simples_nacional: "1"=simples.
        t4.EnquadramentoSimplesNacional = (
            "3" if dados.get("optante_simples_nacional") == "1" else "1"
        )
        # Regime de apuração é obrigatório (erro 802) quando ME/EPP (opção 3).
        # 1 = tributos federais e municipal pelo Simples Nacional.
        if t4.EnquadramentoSimplesNacional == "3":
            t4.RegimeApuracaoSimplesNacional = "1"
        t4.CodigoCidadeLocalPrestacao = str(
            dados_servico.get("municipio_prestacao_servico")
            or self.company_id.partner_id.city_id.ibge_code
            or ""
        )
        t4.CodigoCidadeTomador = str(dados_tomador.get("codigo_municipio") or "")
        t4.CodigoNBS = misc.punctuation_rm(dados_servico.get("codigo_nbs") or "")
        t4.CodigoIndicadorOperacao = (
            dados_servico.get("codigo_indicador_operacao") or ""
        )
        t4.CodigoClassificacaoTributariaIBSCBS = (
            dados_servico.get("ibs_cbs_classificacao_tributaria") or ""
        )
        t4.CodigoSituacaoTributariaIBSCBS = (
            dados_servico.get("ibs_cbs_situacao_tributaria") or ""
        )
        t4.OperacaoUsoConsumoPessoal = "0"
        t4.IndicadorDestinatarioServico = "0"
        return t4

    def _barueri_build_registros_tipo3(self, dados_servico):
        """Um registro tipo 3 por retencao federal com valor."""
        registros = []
        for codigo, campo in BARUERI_RETENCOES:
            valor = _cents(dados_servico.get(campo))
            if valor == "0":
                continue
            t3 = _new_registro(RegistroTipo3)
            t3.CodigoOutrosValores = codigo
            t3.Valor = valor
            registros.append(t3)
        return registros

    def _barueri_build_registro_tipo5(self):
        """Registro tipo 5 so para tomador ente governamental (compra
        governamental): tipo do ente (1 Uniao, 2 Estado, 3 DF, 4 Municipio)."""
        ente = self.public_entity_type or self.partner_id.public_entity_type
        if not ente:
            return None
        t5 = _new_registro(RegistroTipo5)
        t5.TipoEnteGovernamental = ente
        t5.TipoOperacaoEntesGovernamentais = BARUERI_OPERACAO_ENTE_GOVERNAMENTAL
        return t5

    def _barueri_remessa_id(self):
        """Identificacao da remessa (11 digitos, unica por contribuinte)."""
        return "%011d" % int(time.time())

    def _serialize_barueri_lote_rps(self):
        dados = self._prepare_lote_rps()
        dados_servico = self._serialize_barueri_dados_servico()
        dados_tomador = self._serialize_barueri_dados_tomador()

        numero_rps = (
            misc.punctuation_rm(str(self.rps_number or self.document_number or ""))
            or "0"
        )
        data_emissao = dados["data_emissao"]
        serie = dados["serie"] or ""

        t1 = _new_registro(RegistroTipo1)
        t1.InscricaoContribuinte = misc.punctuation_rm(
            self.company_id.partner_id.l10n_br_im_code or ""
        )
        t1.VersaoLayout = BARUERI_LAYOUT_VERSION
        # A identificacao da remessa tem de ser unica por contribuinte. Usar o
        # numero do RPS faz o reenvio de um RPS rejeitado colidir com a remessa
        # anterior (erro 102 - "ja informada em outro arquivo de remessa").
        t1.IdentificacaoRemessaContribuinte = self._barueri_remessa_id()

        t2 = _new_registro(RegistroTipo2)
        t2.TipoRPS = "RPS"
        t2.SerieRPS = serie
        # SerieNFe fica em branco: a numeração da NFS-e é atribuída por Barueri
        # (preenchê-la gera o erro 203 - "Número de Série da Nf-e Inválida").
        t2.NumeroRPS = numero_rps
        t2.DataRPS = data_emissao.split("T")[0].replace("-", "")
        t2.HoraRPS = data_emissao.split("T")[1].replace(":", "")
        # E=Enviado (normal). "N" gera erro 212 - "Situação do RPS Inválida".
        t2.SituacaoRPS = "E"
        # Barueri NÃO usa CNAE: o CodigoServicoPrestado é o código municipal de
        # serviço da PMB (city_taxation_code / codigo_tributacao_municipio), só
        # dígitos. Usar o CNAE aqui gera o erro 216 ("Código de Atividade não
        # encontrada na base da PMB").
        t2.CodigoServicoPrestado = misc.punctuation_rm(
            dados_servico.get("codigo_tributacao_municipio")
            or dados_servico.get("codigo_cnae")
            or ""
        )
        # Local da prestacao (1=no municipio, 2=fora) e vias publicas (2=nao):
        # em branco, Barueri rejeita o registro tipo 4 com o erro 804.
        prestacao = str(dados_servico.get("municipio_prestacao_servico") or "")
        company_city = str(self.company_id.partner_id.city_id.ibge_code or "")
        t2.LocalPrestacaoServico = (
            "2" if prestacao and prestacao != company_city else "1"
        )
        t2.ServicoPrestadoViasPublicas = "2"
        t2.QuantidadeServico = 1
        t2.ValorServico = _cents(dados_servico["valor_servicos"])
        registros_tipo3 = self._barueri_build_registros_tipo3(dados_servico)
        total_retencoes = str(sum(int(t3.Valor) for t3 in registros_tipo3))
        # Soma dos registros 3; o ISS retido nao entra (sem codigo no leiaute).
        t2.ValorTotalRetencoes = total_retencoes
        t2.TomadorEstrangeiro = 2
        t2.ServicoExportacao = 2
        # 1=CPF, 2=CNPJ. Antes ia sempre 2 com o CNPJ, e o tomador pessoa
        # fisica saia sem documento.
        if dados_tomador.get("cnpj"):
            t2.IndicadorCPFCNPJTomador = 2
            t2.CPFCNPJTomador = misc.punctuation_rm(dados_tomador["cnpj"])
        else:
            t2.IndicadorCPFCNPJTomador = 1
            t2.CPFCNPJTomador = misc.punctuation_rm(dados_tomador.get("cpf") or "")
        t2.RazaoSocialNomeTomador = dados_tomador["razao_social"]
        t2.EnderecoLogradouroTomador = dados_tomador["endereco"]
        t2.NumeroLogradouroTomador = dados_tomador["numero"]
        t2.ComplementoLogradouroTomador = dados_tomador.get("complemento") or ""
        t2.BairroLogradouroTomador = dados_tomador["bairro"]
        t2.CidadeLogradouroTomador = dados_tomador["descricao_municipio"]
        t2.UFLogradouroTomador = dados_tomador["uf"]
        t2.CEPLogradouroTomador = misc.punctuation_rm(dados_tomador["cep"] or "")
        t2.EmailTomador = dados_tomador["email"]
        t2.DiscriminacaoServico = dados_servico["discriminacao"]

        t4 = self._barueri_build_registro_tipo4(dados, dados_servico, dados_tomador)
        t5 = self._barueri_build_registro_tipo5()

        t9 = _new_registro(RegistroTipo9)
        registros = [t1, t2, *registros_tipo3, t4] + ([t5] if t5 else []) + [t9]
        t9.NumeroTotalLinhas = len(registros)
        t9.ValorTotalServicos = _cents(dados_servico["valor_servicos"])
        t9.ValorTotalValores = total_retencoes

        # União com CRLF (o exportador nfselib trunca o CaracterFimLinha para '\r').
        conteudo = "\r\n".join(_rec(r) for r in registros) + "\r\n"
        # Barueri exige ISO-8859-1 (latin-1); o base 14 usava UTF-8 (incorreto).
        rps_bytes = conteudo.encode("latin-1", errors="replace")
        return base64.b64encode(rps_bytes)

    def serialize_nfse_barueri(self):
        """Monta o envelope MensagemXML (NFeLoteEnviarArquivo) com o RPS em base64.
        Retorna a string XML pronta para o argumento MensagemXML do webservice.
        InscricaoMunicipal vai SEM pontuação (crua gera R0001)."""
        im = misc.punctuation_rm(self.company_id.partner_id.l10n_br_im_code or "")
        cnpj = misc.punctuation_rm(self.company_id.partner_id.vat or "")
        rps_b64 = self._serialize_barueri_lote_rps().decode("ascii")
        nome_arquivo = f"{self.display_name or self.id}.txt".replace("/", "_")
        return (
            f'<NFeLoteEnviarArquivo xmlns="{BARUERI_NS}">'
            f"<InscricaoMunicipal>{im}</InscricaoMunicipal>"
            f"<CPFCNPJContrib>{cnpj}</CPFCNPJContrib>"
            f"<NomeArquivoRPS>{nome_arquivo}</NomeArquivoRPS>"
            "<ApenasValidaArq>false</ApenasValidaArq>"
            f"<ArquivoRPSBase64>{rps_b64}</ArquivoRPSBase64>"
            "</NFeLoteEnviarArquivo>"
        )

    # ------------------------------------------------------------------
    # Transmissão (self-contained: NÃO usa erpbrasil.processar_documento).
    #
    # A lib erpbrasil.edoc 3.1.1 é incompatível com o webservice atual de
    # Barueri: (a) NFSe._post envia 1 argumento posicional, mas as operações
    # agora exigem 2 (VersaoSchema:int + MensagemXML:string); (b) analisar_retorno
    # espera string mas o zeep devolve objeto; (c) o provedor monta a consulta com
    # NFeLoteStatusArquivo.tcIdentificacaoPrestador, inexistente no nfselib atual.
    # Para não tocar a lib compartilhada (usada por NF-e/DF-e), fazemos a chamada
    # SOAP 2-args diretamente aqui, no nosso módulo.
    # ------------------------------------------------------------------
    def _barueri_cliente(self, processador):
        url = urljoin(processador._url, BARUERI_WSRPS_ENDPOINT)
        return processador._transmissao.cliente(url)

    def _barueri_consulta_lote(self, processador, im, cnpj, protocolo):
        mensagem = (
            f'<NFeLoteStatusArquivo xmlns="{BARUERI_NS}">'
            f"<InscricaoMunicipal>{im}</InscricaoMunicipal>"
            f"<CPFCNPJContrib>{cnpj}</CPFCNPJContrib>"
            f"<ProtocoloRemessa>{protocolo}</ProtocoloRemessa>"
            "</NFeLoteStatusArquivo>"
        )
        with self._barueri_cliente(processador) as cliente:
            return cliente.service["NFeLoteStatusArquivo"](1, mensagem)

    def _barueri_baixa_retorno(self, processador, im, cnpj, nome_arq_retorno):
        mensagem = (
            f'<NFeLoteBaixarArquivo xmlns="{BARUERI_NS}">'
            f"<InscricaoMunicipal>{im}</InscricaoMunicipal>"
            f"<CPFCNPJContrib>{cnpj}</CPFCNPJContrib>"
            f"<NomeArqRetorno>{nome_arq_retorno}</NomeArqRetorno>"
            "</NFeLoteBaixarArquivo>"
        )
        with self._barueri_cliente(processador) as cliente:
            resposta = cliente.service["NFeLoteBaixarArquivo"](1, mensagem)
        conteudo = getattr(resposta, "ArquivoRPSBase64", None)
        if not conteudo:
            return ""
        if not isinstance(conteudo, bytes | bytearray):
            conteudo = base64.b64decode(conteudo)
        return _decode_retorno(bytes(conteudo))

    def _barueri_send_lote(self):
        """Envia o arquivo e devolve (protocolo, mensagem). Nao muda o estado."""
        self.ensure_one()
        processador = self._processador_erpbrasil_nfse()
        mensagem = self.serialize_nfse_barueri()
        _logger.info(
            "NFS-e Barueri %s: envio para %s (ambiente %s)",
            self.display_name,
            processador._url,
            self.nfse_environment,
        )
        with self._barueri_cliente(processador) as cliente:
            resp_envio = cliente.service["NFeLoteEnviarArquivo"](1, mensagem)
        return (
            getattr(resp_envio, "ProtocoloRemessa", None),
            _barueri_parse_mensagens(resp_envio),
        )

    def _barueri_poll(
        self, protocolo, tries=BARUERI_POLL_TRIES, wait=BARUERI_POLL_WAIT
    ):
        """Consulta o lote ate haver arquivo de retorno.
        Devolve (situacao, nome_retorno, retorno_txt)."""
        self.ensure_one()
        processador = self._processador_erpbrasil_nfse()
        im = misc.punctuation_rm(self.company_id.partner_id.l10n_br_im_code or "")
        cnpj = misc.punctuation_rm(self.company_id.partner_id.vat or "")
        situacao = nome_retorno = None
        for tentativa in range(tries):
            if tentativa or wait:
                time.sleep(wait)
            resp_status = self._barueri_consulta_lote(processador, im, cnpj, protocolo)
            arq = getattr(resp_status, "ListaNfeArquivosRPS", None)
            if arq is not None:
                situacao = getattr(arq, "SituacaoArq", None)
                nome_retorno = getattr(arq, "NomeArqRetorno", None)
            if nome_retorno:
                break
        retorno = ""
        if nome_retorno:
            retorno = self._barueri_baixa_retorno(processador, im, cnpj, nome_retorno)
        return situacao, nome_retorno, retorno

    def _barueri_set_protocol(self, protocolo):
        """Grava o protocolo da remessa no evento de autorizacao: o campo
        authorization_protocol do documento e relacionado a ele."""
        if protocolo and self.authorization_event_id:
            self.authorization_event_id.protocol_number = protocolo

    @staticmethod
    def _barueri_erros_retorno(retorno_txt):
        """Resume o arquivo .ERR: cada linha do RPS volta com os codigos de erro
        no fim ("...0000;807;817;"). Devolve ["Registro 4: 807, 817"]."""
        erros = []
        for linha in (retorno_txt or "").splitlines():
            linha = linha.rstrip()
            if not linha.endswith(";"):
                continue
            codigos = []
            for parte in linha.split(";")[:-1]:
                codigo = parte.rstrip()[-3:]
                if codigo.isdigit():
                    codigos.append(codigo)
            if codigos:
                erros.append(f"Registro {linha[0]}: {', '.join(codigos)}")
        return erros

    @staticmethod
    def _barueri_parse_retorno_ok(retorno_txt):
        """Le o arquivo de retorno de sucesso (leiaute de exportacao da NFS-e de
        Barueri, registro tipo 2) e devolve um dict com numero, data, hora,
        codigo de autenticidade, situacao e chave; ou {} se nao houver nota."""
        for linha in (retorno_txt or "").splitlines():
            if linha[:1] != "2" or len(linha) < 67:
                continue
            return {
                "serie": linha[1:5].strip(),
                "numero": linha[5:12].strip(),
                "data": linha[12:20],
                "hora": linha[20:26],
                "verify_code": linha[26:50].strip(),
                "situacao": linha[66:67],
                "chave": linha[1628:1678].strip() if len(linha) >= 1678 else "",
            }
        return {}

    def _document_cancel(self, justificative=None):
        """O cancelamento em Barueri (RPS com situacao "C") ainda nao foi
        implementado. Sem esta trava, o Odoo marcaria a nota como cancelada
        sem avisar a Prefeitura, e a NFS-e continuaria valida la."""
        authorized = (
            self.filtered(filter_oca_nfse)
            .filtered(filter_barueri)
            .filtered(lambda d: d.state_edoc == SITUACAO_EDOC_AUTORIZADA)
        )
        if authorized:
            raise UserError(
                _(
                    "O cancelamento da NFS-e de Barueri ainda nao e transmitido "
                    "pelo Odoo. Cancele a nota %s no portal da Prefeitura de "
                    "Barueri."
                )
                % ", ".join(authorized.mapped("display_name"))
            )
        return super()._document_cancel(justificative)

    def _eletronic_document_send(self):
        # Registros Barueri são tratados aqui; os demais seguem o fluxo padrão.
        barueri_records = self.filtered(filter_oca_nfse).filtered(filter_barueri)
        super(Document, self - barueri_records)._eletronic_document_send()
        for record in barueri_records:
            record._barueri_process_send()
        return

    def _document_status(self):
        """Reconsulta o lote de Barueri que ficou em processamento."""
        result = super()._document_status()
        for record in self.filtered(filter_oca_nfse).filtered(filter_barueri):
            if not record.authorization_protocol or record.state_edoc in (
                SITUACAO_EDOC_AUTORIZADA,
                SITUACAO_EDOC_REJEITADA,
            ):
                continue
            situacao, nome_retorno, retorno = record._barueri_poll(
                record.authorization_protocol, tries=1, wait=0
            )
            record._barueri_apply_result(
                record.authorization_protocol, "", nome_retorno, retorno
            )
            result = record.status_name
        return result

    def _barueri_process_send(self):
        """Envia o lote, GRAVA o protocolo e define o estado conforme o retorno:
        - sem protocolo         -> rejeitada (falha no envio)
        - em processamento      -> enviada (reconsultar pelo botão de situação)
        - retorno .ERR          -> rejeitada + codigos
        - retorno de sucesso    -> autorizada (+ numero/codigo de autenticidade)"""
        self.ensure_one()
        try:
            protocolo, mensagem = self._barueri_send_lote()
            self._barueri_set_protocol(protocolo)
            nome_retorno = retorno = None
            if protocolo:
                _situacao, nome_retorno, retorno = self._barueri_poll(protocolo)
        except Exception as exc:  # noqa: BLE001 - erro de transmissão/rede
            _logger.exception("Erro na transmissão NFS-e Barueri")
            self.write({"edoc_error_message": str(exc)})
            self._change_state(SITUACAO_EDOC_REJEITADA)
            return
        if not protocolo:
            self.write(
                {"edoc_error_message": mensagem or _("Falha no envio (sem protocolo).")}
            )
            self._change_state(SITUACAO_EDOC_REJEITADA)
            return
        self._barueri_apply_result(protocolo, mensagem, nome_retorno, retorno)

    def _barueri_apply_result(self, protocolo, mensagem, nome_retorno, retorno):
        self.ensure_one()
        mensagem = mensagem or ""
        if not nome_retorno:
            self.write(
                {
                    "edoc_error_message": (
                        mensagem + f"\nProtocolo: {protocolo}\n"
                        "Lote em processamento — reconsultar."
                    ).strip(),
                    "status_name": f"Em processamento (protocolo {protocolo})",
                }
            )
            if self.state_edoc != SITUACAO_EDOC_ENVIADA:
                self._change_state(SITUACAO_EDOC_ENVIADA)
            return

        if nome_retorno.upper().endswith(".ERR"):
            erros = self._barueri_erros_retorno(retorno)
            self.write(
                {
                    "edoc_error_message": "\n".join(
                        [m for m in [mensagem, f"Arquivo {nome_retorno}"] + erros if m]
                    ),
                    "status_name": "Rejeitada ({})".format(
                        "; ".join(erros or ["ver retorno"])
                    ),
                }
            )
            self._change_state(SITUACAO_EDOC_REJEITADA)
            return

        nota = self._barueri_parse_retorno_ok(retorno)
        vals = {"status_name": "Autorizada", "edoc_error_message": False}
        if nota.get("numero"):
            vals["document_number"] = nota["numero"]
        if nota.get("verify_code"):
            vals["verify_code"] = nota["verify_code"]
        if nota.get("data") and nota.get("hora"):
            try:
                local = datetime.strptime(nota["data"] + nota["hora"], "%Y%m%d%H%M%S")
                tz = pytz.timezone(self.env.user.tz or "America/Sao_Paulo")
                vals["authorization_date"] = (
                    tz.localize(local).astimezone(pytz.utc).replace(tzinfo=None)
                )
            except ValueError:
                _logger.warning(
                    "NFS-e Barueri %s: data de autorizacao invalida no retorno (%s %s)",
                    self.display_name,
                    nota["data"],
                    nota["hora"],
                )
        if not nota:
            vals["edoc_error_message"] = (
                f"Retorno {nome_retorno} sem registro de NFS-e:\n{retorno}"
            )
        self.write(vals)
        if self.authorization_event_id:
            self.authorization_event_id.set_done(
                status_code=nota.get("situacao") or "A",
                response=vals["status_name"],
                protocol_date=vals.get("authorization_date") or fields.Datetime.now(),
                protocol_number=protocolo,
                file_response_xml=False,
            )
            if retorno:
                # O retorno de Barueri e um TXT posicional, nao um XML.
                self.authorization_event_id._save_event_file(
                    retorno, "txt", authorization=True
                )
        self._change_state(SITUACAO_EDOC_AUTORIZADA)
