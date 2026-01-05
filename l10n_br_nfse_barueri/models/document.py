# Copyright 2023 - KMEE INFORMATICA LTDA
# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import unicodedata
from datetime import datetime

import requests
from nfselib.barueri.NFeLoteEnviarArquivo import NFeLoteEnviarArquivo
from nfselib.barueri.nfse import (
    NFSeRegistroTipo1,
    NFSeRegistroTipo2,
    NFSeRegistroTipo3,
    NFSeRegistroTipo4,
    NFSeRegistroTipo9,
)
from nfselib.barueri.rps import (
    RPS,
    RegistroTipo1,
    RegistroTipo2,
    RegistroTipo3,
    RegistroTipo4,
    RegistroTipo5,
    RegistroTipo9,
)

from odoo import _, api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    MODELO_FISCAL_NFSE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_REJEITADA,
)

from ..constants.barueri import (
    CONSULTAR_NFSE_POR_RPS,
    CONSULTAR_SITUACAO_LOTE_RPS,
    ENVIO_LOTE_RPS,
)


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


def parse_linha_exporta(line: str):
    tipo = line[0]
    if tipo == "1":
        reg = NFSeRegistroTipo1.from_line(line)
    elif tipo == "2":
        reg = NFSeRegistroTipo2.from_line(line)
    elif tipo == "3":
        reg = NFSeRegistroTipo3.from_line(line)
    elif tipo == "4":
        reg = NFSeRegistroTipo4.from_line(line)
    elif tipo == "5":
        reg = NFSeRegistroTipo4.from_line(line)
    elif tipo == "9":
        reg = NFSeRegistroTipo9.from_line(line)
    else:
        raise ValueError(f"Tipo de registro desconhecido: {tipo}")

    return reg


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    url_nfse_barueri = fields.Char(
        string="URL of NFSe Barueri",
        compute="_compute_url_nfse_barueri",
        help="URL to access the Nota Fiscal de Serviços Eletrônicos (NFSe)"
        "from the São Paulo City (Barueri).",
    )
    is_nfse_barueri = fields.Boolean(
        string="Is NFSe Barueri?",
        compute="_compute_is_nfse_barueri",
        help="Technical field to identify if the document is a NFSe Barueri.",
    )

    def _compute_url_nfse_barueri(self):
        for doc in self:
            if not doc.is_nfse_barueri:
                doc.url_nfse_barueri = ""
                continue

            autenticidade = (doc.verify_code or "").strip()
            cnpj_tomador = "".join(
                ch for ch in (doc.partner_id.cnpj_cpf or "") if ch.isdigit()
            )
            if not (autenticidade and cnpj_tomador):
                doc.url_nfse_barueri = ""
                continue
            if doc.nfse_environment == "1":
                base_url = "https://www.barueri.sp.gov.br/nfe/wfimagemNota.aspx"
            else:
                base_url = "https://testeeiss.barueri.sp.gov.br/nfe/wfimagemNota.aspx"

            doc.url_nfse_barueri = (
                f"{base_url}"
                f"?CODIGOAUTENTICIDADE={autenticidade}"
                f"&NUMDOC={cnpj_tomador}"
            )

    def action_open_nfse_barueri(self):
        return {
            "type": "ir.actions.act_url",
            "url": self.url_nfse_barueri,
            "target": "new",
        }

    def _compute_is_nfse_barueri(self):
        for doc in self:
            is_nfse = doc.document_type == "SE"
            is_barueri = doc.company_id.city_id == self.env.ref(
                "l10n_br_base.city_3505708"
            )

            if is_nfse and is_barueri:
                doc.is_nfse_barueri = True
            else:
                doc.is_nfse_barueri = False

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_oca_nfse).filtered(filter_barueri):
            edocs.append(record.serialize_nfse_barueri())
        return edocs

    def _serialize_barueri_dados_servico(self):
        self.fiscal_line_ids.ensure_one()
        dados = self._prepare_dados_servico()
        return dados

    def _serialize_barueri_dados_tomador(self):
        dados = self._prepare_dados_tomador()
        return dados

    def _sem_acento(self, value):
        return (
            unicodedata.normalize("NFKD", value or "")
            .encode("ASCII", "ignore")
            .decode("ASCII")
        )

    def _serialize_barueri_lote_rps(self, cancel=False):
        dados = self._prepare_lote_rps()
        dados_servico = self._serialize_barueri_dados_servico()
        dados_tomador = self._serialize_barueri_dados_tomador()
        # Registro tipo 1 - Cabeçalho do arquivo RPS
        registro_tipo1 = RegistroTipo1()
        registro_tipo1.TipoRegistro = 1
        registro_tipo1.InscricaoContribuinte = self.company_inscr_mun
        registro_tipo1.VersaoLayout = "PMB004"
        if cancel:
            data_base = datetime.now()
            data_emissao = data_base.strftime("%Y-%m-%d")
        else:
            data_emissao = dados["data_emissao"].split("T")[0]
        ano_mes_dia = data_emissao.replace("-", "")
        sequencial = datetime.now().strftime("%f")[-3:]
        registro_tipo1.IdentificacaoRemessaContribuinte = f"{ano_mes_dia}{sequencial}"

        # Registro tipo 2 - Dados do RPS
        registro_tipo2 = RegistroTipo2()
        registro_tipo2.TipoRegistro = 2
        registro_tipo2.TipoRPS = "RPS"
        if cancel:
            registro_tipo2.SituacaoRPS = "C"
            registro_tipo2.NumeroRPS = "0" * 10
            now = datetime.now()
            registro_tipo2.DataRPS = now.strftime("%Y%m%d")
            registro_tipo2.HoraRPS = now.strftime("%H%M%S")
            registro_tipo2.CodigoMotivoCancelamento = "01"
            registro_tipo2.NumeroNFeCancelada = str(int(self.document_number)).zfill(7)
            registro_tipo2.SerieNFeCancelada = ""
            registro_tipo2.DataEmissaoNFeCancelada = self.authorization_date.strftime(
                "%Y%m%d"
            )
            descricao = (self.cancel_reason or "").strip()
            descricao = self._sem_acento(descricao)[:180]
            registro_tipo2.DescricaoCancelamento = descricao
        else:
            numero_rps = str(self.rps_number or "1").zfill(7)
            registro_tipo2.NumeroRPS = f"000{numero_rps}"
            registro_tipo2.DataRPS = (
                dados["data_emissao"].split("T")[0].replace("-", "")
            )
            registro_tipo2.HoraRPS = (
                dados["data_emissao"].split("T")[1].replace(":", "")
            )
            registro_tipo2.SituacaoRPS = "E"
            registro_tipo2.CodigoMotivoCancelamento = ""
            registro_tipo2.NumeroNFeCancelada = ""
            registro_tipo2.SerieNFeCancelada = ""
            registro_tipo2.DataEmissaoNFeCancelada = ""
            registro_tipo2.DescricaoCancelamento = ""
        registro_tipo2.CodigoServicoPrestado = dados_servico[
            "codigo_tributacao_municipio"
        ]
        registro_tipo2.LocalPrestacaoServico = (
            "1"
        )  # String: 1=Município, 2=Fora do Município
        registro_tipo2.ServicoPrestadoViasPublicas = "2"  # String: 1=Sim, 2=Não
        registro_tipo2.EnderecoLogradouroLocalServico = ""
        registro_tipo2.NumeroLogradouroLocalServico = ""
        registro_tipo2.ComplementoLogradouroLocalServico = ""
        registro_tipo2.BairroLogradouroLocalServico = ""
        registro_tipo2.CidadeLogradouroLocalServico = ""
        registro_tipo2.UFLogradouroLocalServico = ""
        registro_tipo2.CEPLogradouroLocalServico = ""
        fiscal_line = self.fiscal_line_ids[0] if self.fiscal_line_ids else None
        quantidade = int(fiscal_line.quantity or 1) if fiscal_line else 1
        valor_servicos_total = dados_servico.get("valor_servicos", 0) or 0
        valor_unitario = (
            valor_servicos_total / quantidade
            if quantidade > 0
            else valor_servicos_total
        )
        valor_unitario_centavos = int(round(float(valor_unitario) * 100))
        registro_tipo2.QuantidadeServico = str(quantidade).zfill(6)
        registro_tipo2.ValorServico = str(valor_unitario_centavos).zfill(15)
        valor_retencoes_total = (
            (dados_servico.get("valor_ir_retido", 0) or 0)
            + (dados_servico.get("valor_pis_retido", 0) or 0)
            + (dados_servico.get("valor_cofins_retido", 0) or 0)
            + (dados_servico.get("valor_csll_retido", 0) or 0)
        )
        valor_retencoes_centavos = int(round(float(valor_retencoes_total) * 100))
        registro_tipo2.ValorTotalRetencoes = str(valor_retencoes_centavos).zfill(15)
        registro_tipo2.TomadorEstrangeiro = "2"  # String: 1=Estrangeiro, 2=Brasileiro
        registro_tipo2.ServicoExportacao = "2"  # String: 1=Exportado, 2=Não exportado
        cnpj_cpf = dados_tomador.get("cnpj") or dados_tomador.get("cpf", "")
        if cnpj_cpf:
            if len(cnpj_cpf) == 14 and cnpj_cpf.isdigit():
                registro_tipo2.IndicadorCPFCNPJTomador = "2"
                registro_tipo2.CPFCNPJTomador = cnpj_cpf.zfill(14)
            elif len(cnpj_cpf) == 11 and cnpj_cpf.isdigit():
                registro_tipo2.IndicadorCPFCNPJTomador = "1"
                registro_tipo2.CPFCNPJTomador = cnpj_cpf.zfill(14)
        else:
            registro_tipo2.IndicadorCPFCNPJTomador = "1"
            registro_tipo2.CPFCNPJTomador = "0" * 14
        registro_tipo2.RazaoSocialNomeTomador = dados_tomador.get("razao_social", "")
        registro_tipo2.EnderecoLogradouroTomador = (
            dados_tomador.get("logradouro", "") or "R Pedra Sabao"
        )
        registro_tipo2.NumeroLogradouroTomador = str(
            dados_tomador.get("numero", "") or "10"
        )
        registro_tipo2.ComplementoLogradouroTomador = str(
            dados_tomador.get("complemento", "") or "N/A"
        )
        registro_tipo2.BairroLogradouroTomador = self._sem_acento(
            dados_tomador.get("bairro", "Bairro N/A")
        )

        registro_tipo2.CidadeLogradouroTomador = self._sem_acento(
            dados_tomador.get("municipio")
        )

        registro_tipo2.UFLogradouroTomador = dados_tomador.get("uf", "")
        cep = (
            str(dados_tomador.get("cep", "") or "")
            .replace("-", "")
            .replace(".", "")
            .replace(" ", "")
        )
        registro_tipo2.CEPLogradouroTomador = cep.zfill(8) if cep else ""
        registro_tipo2.EmailTomador = dados_tomador.get("email", "tomador@email.com")
        registro_tipo2.DiscriminacaoServico = self._sem_acento(
            dados_servico.get("discriminacao", "")
        )
        # Registro tipo 3 - Valores do serviço (retenções)
        registros_tipo3 = []
        retencoes = [
            ("01", "valor_ir_retido"),
            ("02", "valor_pis_retido"),
            ("03", "valor_cofins_retido"),
            ("04", "valor_csll_retido"),
        ]
        for codigo, campo in retencoes:
            valor = dados_servico.get(campo, 0) or 0
            if valor:
                reg = RegistroTipo3()
                reg.TipoRegistro = 3
                reg.CodigoOutrosValores = codigo
                reg.Valor = str(int(round(float(valor) * 100))).zfill(15)
                registros_tipo3.append(reg)

        registro_tipo4 = RegistroTipo4()
        registro_tipo4.TipoRegistro = 4
        registro_tipo4.OptanteSimplesNacional = (
            1
        )  # String: 1=Não optante, 2=MEI, 3=ME/EPP
        registro_tipo4.RegimeApuracaoSN = ""
        registro_tipo4.CodigoCidadeLocalPrestacao = str(
            self.company_id.city_id.ibge_code or ""
        ).zfill(7)
        registro_tipo4.CodigoCidadeTomador = str(
            self.partner_id.city_id.ibge_code or ""
        ).zfill(7)
        registro_tipo4.CodigoNBS = "".join(
            c for c in str(dados_servico.get("codigo_nbs", "")) if c.isdigit()
        )
        registro_tipo4.CodigoIndicadorOperacaoFornecimento = (
            dados_servico.get("codigo_indicador_operacao") or ""
        )

        registro_tipo4.CodigoClassificacaoTributariaIBSCBS = (
            dados_servico.get("codigo_classificacao_tributaria") or ""
        )

        registro_tipo4.CodigoSituacaoTributariaIBSCBS = (
            dados_servico.get("codigo_situacao_tributaria") or ""
        )
        registro_tipo4.OperacaoUsoConsumoPessoal = "0"
        registro_tipo4.IndicadorDestinatarioServico = "0"

        # Registro tipo 5 - Dados complementares do Ambiente de Dados Nacional
        registro_tipo5 = RegistroTipo5()
        registro_tipo5.TipoRegistro = 5
        registro_tipo5.CodigoClassificacaoCreditoPresumidoIBSCBS = ""
        registro_tipo5.TipoEnteGovernamental = ""
        registro_tipo5.TipoOperacaoEntesGovernamentais = "1"
        registro_tipo5.ChaveNFSeReferenciada = ""
        registro_tipo5.CodigoNCMBemMovelLocacao = ""
        registro_tipo5.DescricaoBemMovelLocacao = ""
        registro_tipo5.QuantidadeBemMovelLocacao = ""
        registro_tipo5.IndicadorOperacaoDoacao = ""
        registro_tipo5.DestinatarioServicoEstrangeiro = ""
        registro_tipo5.CPFCNPJDestinatarioServico = ""
        registro_tipo5.RazaoSocialNomeDestinatarioServico = ""
        registro_tipo5.EnderecoLogradouroDestinatarioServico = ""
        registro_tipo5.NumeroLogradouroDestinatarioServico = ""
        registro_tipo5.ComplementoLogradouroDestinatarioServico = ""
        registro_tipo5.BairroLogradouroDestinatarioServico = ""
        registro_tipo5.CidadeLogradouroDestinatarioServico = ""
        registro_tipo5.CodigoCidadeDestinatarioServico = ""
        registro_tipo5.UFLogradouroDestinatarioServico = ""
        registro_tipo5.CodigoPaisDestinatarioServico = ""
        registro_tipo5.CEPLogradouroDestinatarioServico = ""
        registro_tipo5.EmailDestinatarioServico = ""
        registro_tipo5.NIFDestinatario = ""
        registro_tipo5.CodigoEnderecoPostalDestinatarioEstrangeiro = ""
        registro_tipo5.EstadoProvinciaRegiaoDestinatarioEstrangeiro = ""
        # Registro tipo 9 - Rodapé do arquivo RPS
        registros_dados = [registro_tipo1, registro_tipo2]
        if registros_tipo3:
            registros_dados.extend(registros_tipo3)
        registros_dados.append(registro_tipo4)

        registros_dados.append(registro_tipo5)

        numero_total_linhas = len(registros_dados) + 1
        quantidade_total = int(registro_tipo2.QuantidadeServico)
        valor_unitario_centavos = int(registro_tipo2.ValorServico)
        valor_total_servicos_centavos = quantidade_total * valor_unitario_centavos
        valor_total_registro3 = sum(int(r.Valor) for r in registros_tipo3)
        registro_tipo9 = RegistroTipo9()
        registro_tipo9.TipoRegistro = 9
        registro_tipo9.NumeroTotalLinhas = str(numero_total_linhas).zfill(7)
        registro_tipo9.ValorTotalServicos = str(valor_total_servicos_centavos).zfill(15)
        registro_tipo9.ValorTotalValores = str(valor_total_registro3).zfill(15)

        registros_finais = registros_dados + [registro_tipo9]
        rps = RPS(registros_finais).exportar()

        if isinstance(rps, str):
            rps = rps.encode("utf-8")
        if not isinstance(rps, bytes):
            raise ValueError(
                "O conteúdo fornecido para a codificação base64 não está em formato"
                " de bytes."
            )

        return rps

    def serialize_nfse_barueri(self, cancel=False):
        lote_rps = NFeLoteEnviarArquivo(
            InscricaoMunicipal=self.convert_type_nfselib(
                NFeLoteEnviarArquivo, "InscricaoMunicipal", self.company_inscr_mun
            ),
            CPFCNPJContrib=self.convert_type_nfselib(
                NFeLoteEnviarArquivo,
                "CPFCNPJContrib",
                "".join([char for char in self.company_cnpj_cpf if char.isdigit()]),
            ),
            NomeArquivoRPS=self.convert_type_nfselib(
                NFeLoteEnviarArquivo,
                "NomeArquivoRPS",
                "{}{}".format(self.display_name, ".txt"),
            ),
            ApenasValidaArq=self.convert_type_nfselib(
                NFeLoteEnviarArquivo, "ApenasValidaArq", False
            ),
            ArquivoRPSBase64=self.convert_type_nfselib(
                NFeLoteEnviarArquivo,
                "ArquivoRPSBase64",
                self._serialize_barueri_lote_rps(cancel=cancel),
            ),
        )
        return lote_rps

    def _document_status(self):
        mensagem = False
        status = super()._document_status()
        for record in self.filtered(filter_oca_nfse).filtered(filter_barueri):
            processador = record._processador_erpbrasil_nfse()
            protocolo = record.authorization_event_id.lot_receipt_number
            processo = processador.consulta_nfse_rps(
                rps_number=int(record.rps_number),
                rps_serie=record.document_serie,
                rps_type=int(record.rps_type),
                lot_receipt_number=protocolo,
            )

            status, mensagem = processador.analisa_retorno_consulta(processo)
            vals = dict()
            if status == 1 and int(record.status_code) in [-1, -2]:
                vals[
                    "return_filename"
                ] = processo.resposta.ListaNfeArquivosRPS.NomeArqRetorno
                vals["status_name"] = _("Successfully Processed")
                vals["status_code"] = 1
                vals = record._set_response(record, processador, protocolo, vals)

            if status == 2 and int(record.status_code) in [-1, -2]:
                vals[
                    "return_filename"
                ] = processo.resposta.ListaNfeArquivosRPS.NomeArqRetorno
                vals["status_name"] = _("Processed with Error")
                vals["status_code"] = 2
                vals = record._set_response(record, processador, protocolo, vals)

        return mensagem

    def _baixar_xml_nfse(self, autenticidade, cnpj):
        url = (
            "https://testeeiss.barueri.sp.gov.br/nfe/xmlNFe.ashx"
            f"?codigoautenticidade={autenticidade}"
            f"&numdoc={cnpj}"
        )
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()

        return resp.text

    @staticmethod
    def _get_protocolo(record, processador, vals):
        for edoc in record.serialize():
            protocolo = None
            processo = None
            for p in processador.processar_documento(edoc):
                processo = p

                if processo.webservice in ENVIO_LOTE_RPS:
                    record.authorization_event_id.lot_receipt_number = (
                        processo.resposta.ProtocoloRemessa
                    )
                    protocolo = processo.resposta.ProtocoloRemessa

                if processo.webservice in CONSULTAR_NFSE_POR_RPS:
                    if processo.resposta.ProtocoloRemessa is None:
                        mensagem_completa = ""
                        if processo.resposta.ListaMensagemRetorno:
                            lista_msgs = processo.resposta.ListaMensagemRetorno
                            for mr in lista_msgs.MensagemRetorno:
                                correcao = ""
                                if mr.Correcao:
                                    correcao = mr.Correcao

                                mensagem_completa += (
                                    mr.Codigo
                                    + " - "
                                    + mr.Mensagem
                                    + " - Correção: "
                                    + correcao
                                    + "\n"
                                )
                        vals["edoc_error_message"] = mensagem_completa
                        record._change_state(SITUACAO_EDOC_REJEITADA)
                        record.write(vals)
                        return
                    protocolo = processo.resposta.ProtocoloRemessa

                if processo.webservice in CONSULTAR_SITUACAO_LOTE_RPS:
                    vals["status_code"] = int(
                        processo.resposta.ListaNfeArquivosRPS.SituacaoArq
                    )
                    vals[
                        "return_filename"
                    ] = processo.resposta.ListaNfeArquivosRPS.NomeArqRetorno

        return vals, protocolo

    @staticmethod
    def _set_response(record, processador, protocolo, vals):
        processo = processador.baixar_lote_rps(vals.get("return_filename"))

        if processo.resposta:
            mensagem_completa = ""
            if vals.get("status_code") == 2 and processo.resposta.ListaMensagemRetorno:
                lista_msgs = processo.resposta.ListaMensagemRetorno

                if lista_msgs.Codigo != "OK200":
                    mensagem_completa += (
                        lista_msgs.Codigo
                        + " - "
                        + lista_msgs.Mensagem
                        + " - Correção: "
                        + lista_msgs.Correcao
                        + "\n"
                    )
                else:
                    error_messages = {
                        "000": "Layout Inválido",
                        "102": "inválida ou já informada em outro arquivo de remessa",
                        "103": "Versão Incorreta",
                    }

                    file_content = processo.retorno.ArquivoRPSBase64.decode(
                        "utf-8"
                    ).strip()
                    parts = file_content.split(";")
                    values = []
                    for i in range(len(parts) - 1):
                        segment = parts[i]
                        if len(segment) >= 3:
                            last_3 = segment[-3:]
                            values.append(last_3)

                    if values:
                        for value in values:
                            mensagem_completa += (
                                value
                                + " - "
                                + error_messages.get(value, "Erro desconhecido")
                                + " - Correção: "
                                + "Efetuar correção do arquivo"
                                + "\n"
                            )
                vals["edoc_error_message"] = mensagem_completa

                record.write(
                    {
                        "status_name": vals["status_name"],
                        "status_code": vals["status_code"],
                        "edoc_error_message": mensagem_completa,
                    }
                )
                record._change_state(SITUACAO_EDOC_REJEITADA)
            else:
                if vals.get("status_code") == 1:
                    arquivo_bytes = processo.retorno.ArquivoRPSBase64
                    arquivo_texto = arquivo_bytes.decode("latin1")
                    linhas = arquivo_texto.splitlines()
                    registros_exporta = [parse_linha_exporta(linha) for linha in linhas]

                    nfse_number = registros_exporta[1].campos[2].valor
                    nfse_date = registros_exporta[1].campos[3].valor
                    nfse_time = registros_exporta[1].campos[4].valor
                    nfse_auth_code = registros_exporta[1].campos[5].valor
                    nfse_status = registros_exporta[1].campos[10].valor
                    nfse_cnpj_cpf = registros_exporta[1].campos[14].valor

                    vals["authorization_date"] = datetime.strptime(
                        nfse_date + nfse_time, "%Y%m%d%H%M%S"
                    )

                    record.write(
                        {
                            "verify_code": nfse_auth_code,
                            "document_number": nfse_number,
                            "authorization_date": vals["authorization_date"],
                            "status_name": vals["status_name"],
                            "status_code": vals["status_code"],
                        }
                    )

                    xml_file = record._baixar_xml_nfse(nfse_auth_code, nfse_cnpj_cpf)

                    if nfse_status == "A":
                        record.authorization_event_id.set_done(
                            status_code=vals["status_code"],
                            response=vals["status_name"],
                            protocol_date=vals["authorization_date"],
                            protocol_number=protocolo,
                            file_response_xml=xml_file,
                        )
                        record._change_state(SITUACAO_EDOC_AUTORIZADA)
                        record.make_pdf()

                    if nfse_status == "C":
                        event = record.event_ids.create_event_save_xml(
                            company_id=record.company_id,
                            environment=(
                                EVENT_ENV_PROD
                                if record.nfse_environment == "1"
                                else EVENT_ENV_HML
                            ),
                            event_type="2",
                            xml_file=xml_file,
                            document_id=record,
                        )
                        event.write(
                            {
                                "status_code": 2,
                                "response": _("Processado com Sucesso"),
                                "protocol_number": protocolo,
                                "protocol_date": fields.Datetime.now(),
                                "state": "done",
                            }
                        )
                        record.cancel_event_id = event
                        record.state_edoc = SITUACAO_EDOC_CANCELADA
        return vals

    def _eletronic_document_send(self):
        super()._eletronic_document_send()
        for record in self.filtered(filter_oca_nfse).filtered(filter_barueri):
            processador = record._processador_erpbrasil_nfse()

            protocolo = record.authorization_protocol
            vals = dict()

            if not protocolo:
                vals, protocolo = record._get_protocolo(record, processador, vals)

            else:
                vals["status_code"] = 0

            if vals.get("status_code") == -1:
                vals["status_name"] = _("Batch not yet processed")
                record._change_state(SITUACAO_EDOC_ENVIADA)

            elif vals.get("status_code") == -2:
                vals["status_name"] = _("Batch not yet processed")
                record._change_state(SITUACAO_EDOC_ENVIADA)

            elif vals.get("status_code") == 0:
                vals["status_name"] = _("Validated")

            elif vals.get("status_code") == 1:
                vals["status_name"] = _("Successfully Processed")
                vals["authorization_protocol"] = protocolo

            elif vals.get("status_code") == 2:
                vals["status_name"] = _("Processed with Error")

            if vals.get("status_code") in (1, 2):
                vals = record._set_response(record, processador, protocolo, vals)

            if "return_filename" in vals:
                vals.pop("return_filename")
            record.write(vals)
        return

    def _cancel_document_barueri(self):
        for record in self.filtered(filter_oca_nfse).filtered(filter_barueri):
            processador = record._processador_erpbrasil_nfse()
            edoc = record.serialize_nfse_barueri(cancel=True)
            processo_envio = processador.envia_documento(edoc)

            protocolo = processo_envio.resposta.ProtocoloRemessa
            if not protocolo:
                return False
            record.authorization_event_id.write(
                {
                    "lot_receipt_number": protocolo,
                }
            )
            processo_consulta = processador.consulta_nfse_rps(
                rps_number=int(record.rps_number),
                rps_serie=record.document_serie,
                rps_type=int(record.rps_type),
                lot_receipt_number=protocolo,
            )
            status, _mensagem = processador.analisa_retorno_consulta(processo_consulta)
            if status == 0:
                return False
            if status in (-1, -2):
                record._change_state(SITUACAO_EDOC_ENVIADA)
                record.status_code = -2
                record.status_name = _("Cancel batch not yet processed")
                return False

            nome_arquivo = (
                processo_consulta.resposta
                and processo_consulta.resposta.ListaNfeArquivosRPS
                and processo_consulta.resposta.ListaNfeArquivosRPS.NomeArqRetorno
            )

            if not nome_arquivo:
                return False

            processo_retorno = processador.baixar_lote_rps(nome_arquivo)
            if not processo_retorno.retorno:
                return False

            arquivo = processo_retorno.retorno.ArquivoRPSBase64.decode("latin1")
            linhas = arquivo.splitlines()
            registros = [parse_linha_exporta(linha) for linha in linhas]

            nfse_status = registros[1].campos[10].valor
            if nfse_status == "C":
                event = record.event_ids.create_event_save_xml(
                    company_id=record.company_id,
                    environment=(
                        EVENT_ENV_PROD
                        if record.nfse_environment == "1"
                        else EVENT_ENV_HML
                    ),
                    event_type="2",
                    xml_file=processo_envio.envio_xml,
                    document_id=record,
                )
                event.write(
                    {
                        "status_code": 2,
                        "response": _("Processado com Sucesso"),
                        "protocol_number": protocolo,
                        "protocol_date": fields.Datetime.now(),
                        "state": "done",
                    }
                )
                record.cancel_event_id = event
                record.state_edoc = SITUACAO_EDOC_CANCELADA
                return True
            return False

    def _exec_before_SITUACAO_EDOC_CANCELADA(self, old_state, new_state):
        super()._exec_before_SITUACAO_EDOC_CANCELADA(old_state, new_state)
        return (
            self.filtered(filter_oca_nfse)
            .filtered(filter_barueri)
            ._cancel_document_barueri()
        )

    @api.model
    def _cron_document_status_barueri(self):
        """Scheduled method to check the status of sent NFSe documents.

        Parameters:
            None.

        Returns:
            None. Updates the status of each document based
            on the NFSe provider's response.
        """
        records = (
            self.search([("state", "in", ["enviada"])], limit=25)
            .filtered(filter_oca_nfse)
            .filtered(filter_barueri)
        )
        if records:
            records._document_status()
