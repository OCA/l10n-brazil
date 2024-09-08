# Copyright 2023 - KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from nfselib.barueri.NFeLoteEnviarArquivo import NFeLoteEnviarArquivo
from nfselib.barueri.rps import RPS, RegistroTipo2

from odoo import _, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFSE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_REJEITADA,
)

from ..constants.barueri import CONSULTAR_NFSE_POR_RPS, CONSULTAR_SITUACAO_LOTE_RPS


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


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

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

    def _serialize_barueri_lote_rps(self):
        dados = self._prepare_lote_rps()
        dados_servico = self._serialize_barueri_dados_servico()
        dados_tomador = self._serialize_barueri_dados_tomador()
        registro_tipo2 = RegistroTipo2()
        registro_tipo2.SerieNFe = dados["serie"]
        registro_tipo2.DataRPS = dados["data_emissao"].split("T")[0].replace("-", "")
        registro_tipo2.HoraRPS = dados["data_emissao"].split("T")[1].replace(":", "")
        registro_tipo2.SituacaoRPS = "E"
        registro_tipo2.CodigoServicoPrestado = dados_servico["codigo_cnae"]
        registro_tipo2.QuantidadeServico = 1
        registro_tipo2.ValorServico = dados_servico["valor_servicos"]
        registro_tipo2.ValorTotalRetencoes = self.amount_tax_withholding
        registro_tipo2.TomadorEstrangeiro = 2
        registro_tipo2.IndicadorCPFCNPJTomador = 2
        registro_tipo2.CPFCNPJTomador = dados_tomador["cnpj"]
        registro_tipo2.RazaoSocialNomeTomador = dados_tomador["razao_social"]
        registro_tipo2.EnderecoLogradouroTomador = dados_tomador["endereco"]
        registro_tipo2.NumeroLogradouroTomador = dados_tomador["numero"]
        registro_tipo2.ComplementoLogradouroTomador = dados_tomador["complemento"]
        registro_tipo2.BairroLogradouroTomador = dados_tomador["bairro"]
        registro_tipo2.CidadeLogradouroTomador = dados_tomador["descricao_municipio"]
        registro_tipo2.UFLogradouroTomador = dados_tomador["uf"]
        registro_tipo2.CEPLogradouroTomador = dados_tomador["cep"]
        registro_tipo2.EmailTomador = dados_tomador["email"]
        registro_tipo2.DiscriminacaoServico = dados_servico["discriminacao"]
        rps = RPS([registro_tipo2]).exportar()

        if isinstance(rps, str):
            rps = rps.encode("utf-8")
        if not isinstance(rps, bytes):
            raise ValueError(
                "O conteúdo fornecido para a codificação base64 não está em formato"
                " de bytes."
            )

        rps = base64.b64encode(rps)
        return rps

    def serialize_nfse_barueri(self):
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
                self._serialize_barueri_lote_rps(),
            ),
        )
        return lote_rps

    def _document_status(self):
        status = super()._document_status()
        for record in self.filtered(filter_oca_nfse).filtered(filter_barueri):
            processador = record._processador_erpbrasil_nfse()
            processo = processador.consulta_nfse_rps(
                rps_number=int(record.rps_number),
                rps_serie=record.document_serie,
                rps_type=int(record.rps_type),
            )

            status = _(
                processador.analisa_retorno_consulta(
                    processo,
                    record.document_number,
                    record.company_cnpj_cpf,
                    record.company_legal_name,
                )
            )
        return status

    @staticmethod
    def _get_protocolo(record, processador, vals):
        for edoc in record.serialize():
            processo = None
            for p in processador.processar_documento(edoc):
                processo = p

                if processo.webservice in CONSULTAR_NFSE_POR_RPS:
                    if processo.resposta.Protocolo is None:
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
                    protocolo = processo.resposta.Protocolo

            if processo.webservice in CONSULTAR_SITUACAO_LOTE_RPS:
                vals["status_code"] = processo.resposta.Situacao

        return vals, protocolo

    @staticmethod
    def _set_response(record, processador, protocolo, vals):
        processo = processador.consultar_lote_rps(protocolo)

        if processo.resposta:
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
            if vals.get("status_code") == 3:
                record._change_state(SITUACAO_EDOC_REJEITADA)

        if processo.resposta.ListaNfse:
            xml_file = processo.retorno
            for comp in processo.resposta.ListaNfse.CompNfse:
                vals["document_number"] = comp.Nfse.InfNfse.Numero
                vals["authorization_date"] = comp.Nfse.InfNfse.DataEmissao
                vals["verify_code"] = comp.Nfse.InfNfse.CodigoVerificacao
            record.authorization_event_id.set_done(
                status_code=vals["status_code"],
                response=vals["status_name"],
                protocol_date=vals["authorization_date"],
                protocol_number=protocolo,
                file_response_xml=xml_file,
            )
            record._change_state(SITUACAO_EDOC_AUTORIZADA)

        return vals

    def _eletronic_document_send(self):
        super()._eletronic_document_send()
        for record in self.filtered(filter_oca_nfse).filtered(filter_barueri):
            processador = record._processador_erpbrasil_nfse()

            protocolo = record.authorization_protocol
            vals = dict()

            if not protocolo:
                vals, protocolo = self._get_protocolo(record, processador, vals)

            else:
                vals["status_code"] = 4

            if vals.get("status_code") == 1:
                vals["status_name"] = _("Not received")

            elif vals.get("status_code") == 2:
                vals["status_name"] = _("Batch not yet processed")

            elif vals.get("status_code") == 3:
                vals["status_name"] = _("Processed with Error")

            elif vals.get("status_code") == 4:
                vals["status_name"] = _("Successfully Processed")
                vals["authorization_protocol"] = protocolo

            if vals.get("status_code") in (3, 4):
                vals = self._set_response(record, processador, protocolo, vals)

            record.write(vals)
        return
