# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import xml.etree.ElementTree as ET
from datetime import datetime

from erpbrasil.base import misc
from nfselib.paulistana.v02.PedidoEnvioLoteRPS import (
    CabecalhoType,
    PedidoEnvioLoteRPS,
    tpChaveRPS,
    tpCPFCNPJ,
    tpEndereco,
    tpRPS,
)
from unidecode import unidecode

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    MODELO_FISCAL_NFSE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_REJEITADA,
)

from ..constants.paulistana import CONSULTA_LOTE, ENVIO_LOTE_RPS


def filter_oca_nfse(record):
    if record.processador_edoc == PROCESSADOR_OCA and record.document_type_id.code in [
        MODELO_FISCAL_NFSE,
    ]:
        return True
    return False


def filter_paulistana(record):
    if record.company_id.provedor_nfse == "paulistana":
        return True
    return False


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    url_nfse_paulistana = fields.Char(
        string="URL of NFSe Paulistana",
        compute="_compute_url_nfse_paulistana",
        help="URL to access the Nota Fiscal de Serviços Eletrônicos (NFSe)"
        "from the São Paulo City (Paulistana).",
    )
    is_nfse_paulistana = fields.Boolean(
        string="Is NFSe Paulistana?",
        compute="_compute_is_nfse_paulistana",
        help="Technical field to identify if the document is a NFSe Paulistana.",
    )

    def _compute_url_nfse_paulistana(self):
        for doc in self:
            # requeried fields for the url
            nf = doc.document_number
            inscricao = doc.company_id.l10n_br_im_code
            verificacao = doc.verify_code

            # skip if any of the required fields is empty
            if not all([nf, inscricao, verificacao]):
                doc.url_nfse_paulistana = ""
                continue

            nfse_print_url = (
                "https://nfe.prefeitura.sp.gov.br/contribuinte/notaprint.aspx?"
                f"nf={nf}&inscricao={inscricao}&verificacao={verificacao}"
            )
            doc.url_nfse_paulistana = nfse_print_url

    def action_open_nfse_paulistana(self):
        return {
            "type": "ir.actions.act_url",
            "url": self.url_nfse_paulistana,
            "target": "new",
        }

    def _compute_is_nfse_paulistana(self):
        for doc in self:
            is_nfse = doc.document_type == "SE"
            is_paulistana = doc.company_id.city_id == self.env.ref(
                "l10n_br_base.city_3550308"
            )
            use_city_pdf = doc.company_id.nfse_use_city_pdf
            doc.is_nfse_paulistana = bool(is_nfse and is_paulistana and use_city_pdf)

    def _convert_type_nfselib_paulistana(self, class_object, object_filed, value):
        if value is None:
            return value

        value_type = ""
        for field in class_object().member_data_items_:
            if field.name == object_filed:
                value_type = field.child_attrs.get("type", "").replace("xs:", "")
                break

        if value_type in ("int", "long", "byte", "nonNegativeInteger"):
            return int(value)
        elif value_type == "decimal":
            return round(float(value), 2)
        elif value_type == "string":
            return str(value)
        else:
            return value

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_oca_nfse).filtered(filter_paulistana):
            edocs.append(record.serialize_nfse_paulistana())
        return edocs

    def serialize_nfse_paulistana(self):
        dados_lote_rps = self._prepare_lote_rps()
        dados_servico = self._prepare_dados_servico()
        lote_rps = PedidoEnvioLoteRPS(
            Cabecalho=self._serialize_cabecalho(dados_lote_rps),
            RPS=[self._serialize_lote_rps(dados_lote_rps, dados_servico)],
        )
        return lote_rps

    def _serialize_cabecalho(self, dados_lote_rps):
        return CabecalhoType(
            Versao=self._convert_type_nfselib_paulistana(CabecalhoType, "Versao", 1),
            CPFCNPJRemetente=tpCPFCNPJ(
                CNPJ=self._convert_type_nfselib_paulistana(
                    CabecalhoType, "tpCPFCNPJ", dados_lote_rps["cnpj"]
                )
            ),
            transacao=False,  # TODO: Verficar origem do dado
            dtInicio=self._convert_type_nfselib_paulistana(
                CabecalhoType,
                "dtInicio",
                dados_lote_rps["date_in_out"].split("T", 1)[0],
            ),
            dtFim=self._convert_type_nfselib_paulistana(
                CabecalhoType, "dtFim", dados_lote_rps["date_in_out"].split("T", 1)[0]
            ),
            QtdRPS=self._convert_type_nfselib_paulistana(CabecalhoType, "QtdRPS", "1"),
            ValorTotalServicos=self._convert_type_nfselib_paulistana(
                CabecalhoType, "ValorTotalServicos", dados_lote_rps["total_recebido"]
            ),
            ValorTotalDeducoes=self._convert_type_nfselib_paulistana(
                CabecalhoType, "ValorTotalDeducoes", dados_lote_rps["carga_tributaria"]
            ),
        )

    def _serialize_lote_rps(self, dados_lote_rps, dados_servico):
        dados_tomador = self._prepare_dados_tomador()
        return tpRPS(
            Assinatura=self.assinatura_rps(
                dados_lote_rps, dados_servico, dados_tomador
            ),
            ChaveRPS=tpChaveRPS(
                InscricaoPrestador=self._convert_type_nfselib_paulistana(
                    tpChaveRPS,
                    "InscricaoPrestador",
                    dados_lote_rps["inscricao_municipal"].zfill(8),
                ),
                SerieRPS=self._convert_type_nfselib_paulistana(
                    tpChaveRPS, "SerieRPS", dados_lote_rps["serie"]
                ),
                NumeroRPS=self._convert_type_nfselib_paulistana(
                    tpChaveRPS, "NumeroRPS", dados_lote_rps["numero"]
                ),
            ),
            TipoRPS=self._map_type_rps(dados_lote_rps["tipo"]),
            DataEmissao=self._convert_type_nfselib_paulistana(
                tpRPS, "DataEmissao", dados_lote_rps["data_emissao"].split("T", 1)[0]
            ),
            StatusRPS=self._convert_type_nfselib_paulistana(tpRPS, "StatusRPS", "N"),
            TributacaoRPS=self._convert_type_nfselib_paulistana(
                tpRPS,
                "TributacaoRPS",
                self._map_taxation_rps(dados_lote_rps["natureza_operacao"]),
            ),
            ValorServicos=self._convert_type_nfselib_paulistana(
                tpRPS, "ValorServicos", dados_servico["valor_servicos"]
            ),
            ValorDeducoes=self._convert_type_nfselib_paulistana(
                tpRPS, "ValorDeducoes", dados_servico["valor_deducoes"]
            ),
            ValorPIS=self._convert_type_nfselib_paulistana(
                tpRPS, "ValorPIS", dados_servico["valor_pis_retido"]
            ),
            ValorCOFINS=self._convert_type_nfselib_paulistana(
                tpRPS, "ValorCOFINS", dados_servico["valor_cofins_retido"]
            ),
            ValorINSS=self._convert_type_nfselib_paulistana(
                tpRPS, "ValorINSS", dados_servico["valor_inss_retido"]
            ),
            ValorIR=self._convert_type_nfselib_paulistana(
                tpRPS, "ValorIR", dados_servico["valor_ir_retido"]
            ),
            ValorCSLL=self._convert_type_nfselib_paulistana(
                tpRPS, "ValorCSLL", dados_servico["valor_csll_retido"]
            ),
            CodigoServico=self._convert_type_nfselib_paulistana(
                tpRPS, "CodigoServico", dados_servico["codigo_tributacao_municipio"]
            ),
            AliquotaServicos=self._convert_type_nfselib_paulistana(
                tpRPS, "AliquotaServicos", dados_servico["aliquota"]
            ),
            ISSRetido="true" if dados_servico["iss_retido"] == "1" else "false",
            # FIXME: Hardcoded
            CPFCNPJTomador=self._convert_type_nfselib_paulistana(
                tpRPS,
                "CPFCNPJTomador",
                tpCPFCNPJ(CNPJ=dados_tomador["cnpj"], CPF=dados_tomador["cpf"]),
            ),
            InscricaoMunicipalTomador=self._convert_type_nfselib_paulistana(
                tpRPS,
                "InscricaoMunicipalTomador",
                dados_tomador["inscricao_municipal"],
            )
            if dados_tomador["codigo_municipio"]
            == int(f"{self.company_id.partner_id.city_id.ibge_code}")
            else None,
            InscricaoEstadualTomador=self._convert_type_nfselib_paulistana(
                tpRPS, "InscricaoEstadualTomador", dados_tomador["inscricao_estadual"]
            ),
            RazaoSocialTomador=self._convert_type_nfselib_paulistana(
                tpRPS, "RazaoSocialTomador", dados_tomador["razao_social"]
            ),
            EnderecoTomador=tpEndereco(
                Logradouro=self._convert_type_nfselib_paulistana(
                    tpEndereco, "Logradouro", dados_tomador["endereco"]
                ),
                NumeroEndereco=self._convert_type_nfselib_paulistana(
                    tpEndereco, "NumeroEndereco", dados_tomador["numero"]
                ),
                ComplementoEndereco=self._convert_type_nfselib_paulistana(
                    tpEndereco, "ComplementoEndereco", dados_tomador["complemento"]
                ),
                Bairro=self._convert_type_nfselib_paulistana(
                    tpEndereco, "Bairro", dados_tomador["bairro"]
                ),
                Cidade=self._convert_type_nfselib_paulistana(
                    tpEndereco, "Cidade", dados_tomador["codigo_municipio"]
                ),
                UF=self._convert_type_nfselib_paulistana(
                    tpEndereco, "UF", dados_tomador["uf"]
                ),
                CEP=self._convert_type_nfselib_paulistana(
                    tpEndereco, "CEP", dados_tomador["cep"]
                ),
            ),
            EmailTomador=self._convert_type_nfselib_paulistana(
                tpRPS, "EmailTomador", dados_tomador["email"]
            ),
            Discriminacao=self._convert_type_nfselib_paulistana(
                tpRPS,
                "Discriminacao",
                unidecode(
                    dados_servico["discriminacao"]
                    + (
                        "|{}|".format(self.fiscal_additional_data.replace("\n", "|"))
                        if self.fiscal_additional_data
                        else ""
                    )
                ),
            ),
            ValorCargaTributaria=self._convert_type_nfselib_paulistana(
                tpRPS,
                "ValorCargaTributaria",
                dados_lote_rps["carga_tributaria_estimada"],
            ),
            FonteCargaTributaria=self._convert_type_nfselib_paulistana(
                tpRPS, "FonteCargaTributaria", "IBPT"
            ),
            MunicipioPrestacao=self._convert_type_nfselib_paulistana(
                CabecalhoType,
                "Versao",
                self._map_provision_municipality(
                    dados_lote_rps["natureza_operacao"],
                    dados_servico["codigo_municipio"],
                ),
            ),
        )

    def _serialize_rps(self, dados):
        return tpRPS(
            InscricaoMunicipalTomador=self._convert_type_nfselib_paulistana(
                tpRPS, "InscricaoMunicipalTomador", dados["inscricao_municipal"]
            ),
            CPFCNPJTomador=tpCPFCNPJ(
                Cnpj=self._convert_type_nfselib_paulistana(
                    tpCPFCNPJ, "Cnpj", dados["cnpj"]
                ),
                Cpf=self._convert_type_nfselib_paulistana(
                    tpCPFCNPJ, "Cpf", dados["cpf"]
                ),
            ),
            RazaoSocialTomador=self._convert_type_nfselib_paulistana(
                tpRPS, "RazaoSocialTomador", dados["razao_social"]
            ),
            EnderecoTomador=tpEndereco(
                Logradouro=self._convert_type_nfselib_paulistana(
                    tpEndereco, "Logradouro", dados["endereco"]
                ),
                NumeroEndereco=self._convert_type_nfselib_paulistana(
                    tpEndereco, "NumeroEndereco", dados["numero"]
                ),
                ComplementoEndereco=self._convert_type_nfselib_paulistana(
                    tpEndereco, "ComplementoEndereco", dados["complemento"]
                ),
                Bairro=self._convert_type_nfselib_paulistana(
                    tpEndereco, "Bairro", dados["bairro"]
                ),
                Cidade=self._convert_type_nfselib_paulistana(
                    tpEndereco, "Cidade", dados["codigo_municipio"]
                ),
                UF=self._convert_type_nfselib_paulistana(tpEndereco, "UF", dados["uf"]),
                CEP=self._convert_type_nfselib_paulistana(
                    tpEndereco, "CEP", dados["cep"]
                ),
            )
            or None,
        )

    def assinatura_rps(self, dados_lote_rps, dados_servico, dados_tomador):
        assinatura = ""

        assinatura += dados_lote_rps["inscricao_municipal"].zfill(8)
        assinatura += dados_lote_rps["serie"].ljust(5, " ")
        assinatura += dados_lote_rps["numero"].zfill(12)
        assinatura += datetime.strptime(
            dados_lote_rps["data_emissao"], "%Y-%m-%dT%H:%M:%S"
        ).strftime("%Y%m%d")
        assinatura += self._map_taxation_rps(dados_lote_rps["natureza_operacao"])
        assinatura += "N"  # Corrigir - Verificar status do RPS
        assinatura += "S" if dados_servico["iss_retido"] == "1" else "N"
        assinatura += (
            "{:.2f}".format(dados_servico["valor_servicos"]).replace(".", "").zfill(15)
        )
        assinatura += (
            "{:.2f}".format(dados_lote_rps["carga_tributaria"])
            .replace(".", "")
            .zfill(15)
        )
        assinatura += dados_servico["codigo_tributacao_municipio"].zfill(5)
        assinatura += "2" if dados_tomador["cnpj"] else "1"
        assinatura += (dados_tomador["cnpj"] or dados_tomador["cpf"]).zfill(14)
        # assinatura += '3'
        # assinatura += ''.zfill(14)
        # assinatura += 'N'

        return assinatura

    def _map_taxation_rps(self, operation_nature):
        # FIXME: Lidar com diferença de tributado em São Paulo ou não
        dict_taxation = {
            "1": "T",
            "2": "F",
            "3": "A",
            "4": "R",
            "5": "X",
            "6": "X",
        }

        return dict_taxation[operation_nature]

    def _map_provision_municipality(self, operation_nature, municipal_code):
        if operation_nature == "1":
            return None
        else:
            return municipal_code

    def _map_type_rps(self, rps_type):
        dict_type_rps = {
            "1": "RPS",
            "2": "RPS-M",
            "3": "RPS-C",
        }

        return dict_type_rps[rps_type]

    def _eletronic_document_send(self):
        super()._eletronic_document_send()
        for record in self.filtered(filter_oca_nfse).filtered(filter_paulistana):
            processador = record._processador_erpbrasil_nfse()

            protocolo = record.authorization_protocol
            vals = dict()

            if not protocolo:
                for edoc in record.serialize():
                    processo = None
                    for p in processador.processar_documento(edoc):
                        processo = p
                        retorno = ET.fromstring(processo.retorno)

                        if processo.webservice in CONSULTA_LOTE:
                            if processo.resposta.Cabecalho.Sucesso:
                                nfse = retorno.find(".//NFe")
                                # TODO: Verificar resposta do ConsultarLote
                                vals["document_number"] = nfse.find(".//NumeroNFe").text
                                vals["authorization_date"] = nfse.find(
                                    ".//DataEmissaoRPS"
                                ).text
                                vals["verify_code"] = nfse.find(
                                    ".//CodigoVerificacao"
                                ).text
                                record.authorization_event_id.set_done(
                                    status_code=4,
                                    response=vals["status_name"],
                                    protocol_date=vals["authorization_date"],
                                    protocol_number=protocolo,
                                    file_response_xml=processo.retorno,
                                )
                            continue

                        if processo.webservice in ENVIO_LOTE_RPS:
                            if retorno is not None:
                                if processo.resposta.Cabecalho.Sucesso:
                                    record._change_state(SITUACAO_EDOC_AUTORIZADA)
                                    vals["status_name"] = _("Procesado com Sucesso")
                                    vals["status_code"] = 4
                                    vals["edoc_error_message"] = ""
                                else:
                                    mensagem_erro = ""
                                    for erro in retorno.findall("Erro"):
                                        codigo = erro.find("Codigo").text
                                        descricao = erro.find("Descricao").text
                                        mensagem_erro += (
                                            codigo + " - " + descricao + "\n"
                                        )

                                    vals["edoc_error_message"] = mensagem_erro
                                    vals["status_name"] = _("Procesado com Erro")
                                    vals["status_code"] = 3
                                    record._change_state(SITUACAO_EDOC_REJEITADA)
                record.write(vals)
        return

    def _document_status(self):
        status = super()._document_status()
        for record in self.filtered(filter_oca_nfse).filtered(filter_paulistana):
            vals = dict()
            processador = record._processador_erpbrasil_nfse()
            processo = processador.consulta_nfse_rps(
                numero_rps=record.rps_number,
                serie_rps=record.document_serie,
                insc_prest=misc.punctuation_rm(
                    record.company_id.partner_id.l10n_br_im_code or ""
                )
                or None,
                cnpj_prest=misc.punctuation_rm(record.company_id.partner_id.vat),
            )

            consulta = processador.analisa_retorno_consulta(processo)
            retorno = ET.fromstring(processo.retorno)

            if processo.webservice in CONSULTA_LOTE:
                if processo.resposta.Cabecalho.Sucesso:
                    nfse = retorno.find(".//NFe")

                    vals["document_number"] = nfse.find(".//NumeroNFe").text
                    vals["authorization_date"] = nfse.find(".//DataEmissaoRPS").text
                    vals["verify_code"] = nfse.find(".//CodigoVerificacao").text
                    vals["status_name"] = _("Procesado com Sucesso")
                    vals["status_code"] = 4
                    vals["edoc_error_message"] = ""

                    record.authorization_event_id.set_done(
                        status_code=4,
                        response=vals["status_name"],
                        protocol_date=vals["authorization_date"],
                        protocol_number=nfse.find(".//CodigoVerificacao").text,
                        file_response_xml=processo.retorno,
                    )

                    record._change_state(SITUACAO_EDOC_AUTORIZADA)
                    record.write(vals)
            status = _(consulta)
        return status

    def cancel_document_paulistana(self):
        def doc_dict(record):
            return {
                "numero_nfse": record.document_number,
                "codigo_verificacao": record.verify_code,
            }

        status = True
        for record in self.filtered(filter_oca_nfse).filtered(filter_paulistana):
            processador = record._processador_erpbrasil_nfse()
            processo = processador.cancela_documento(doc_numero=doc_dict(record))

            status, message = processador.analisa_retorno_cancelamento_paulistana(
                processo
            )

            if not status:
                raise UserError(_(message))

            record.cancel_event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=(
                    EVENT_ENV_PROD if record.nfse_environment == "1" else EVENT_ENV_HML
                ),
                event_type="2",
                xml_file=processo.envio_xml,
                document_id=record,
            )

        return status

    def _before_document_cancel(self):
        result = super()._before_document_cancel()
        if not self.filtered(filter_oca_nfse).filtered(filter_paulistana):
            return result
        return self.cancel_document_paulistana()
