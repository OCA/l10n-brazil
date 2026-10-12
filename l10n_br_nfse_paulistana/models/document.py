# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import xml.etree.ElementTree as ET
from datetime import datetime

from erpbrasil.base import misc
from nfselib.paulistana.v03.PedidoEnvioLoteRPS_v02 import (
    CabecalhoType,
    PedidoEnvioLoteRPS,
    tpChaveRPS,
    tpCPFCNPJNIF,
    tpEndereco,
    tpGIBSCBS,
    tpIBSCBS,
    tpRPS,
    tpTrib,
    tpValores,
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
            nf = doc.document_number
            inscricao = doc.company_id.l10n_br_im_code
            verificacao = doc.verify_code
            if not all([nf, inscricao, verificacao]):
                doc.url_nfse_paulistana = ""
                continue
            doc.url_nfse_paulistana = (
                "https://nfe.prefeitura.sp.gov.br/contribuinte/notaprint.aspx?"
                f"nf={nf}&inscricao={inscricao}&verificacao={verificacao}"
            )

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

    def convert_type_nfselib(self, class_object, object_filed, value):
        if value is None or value is False:
            return None

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
            Versao=self.convert_type_nfselib(CabecalhoType, "Versao", 2),
            CPFCNPJRemetente=tpCPFCNPJNIF(
                CNPJ=self.convert_type_nfselib(
                    tpCPFCNPJNIF, "CNPJ", dados_lote_rps["cnpj"]
                )
            ),
            transacao=False,  # TODO: Verficar origem do dado
            dtInicio=self.convert_type_nfselib(
                CabecalhoType,
                "dtInicio",
                dados_lote_rps["date_in_out"].split("T", 1)[0],
            ),
            dtFim=self.convert_type_nfselib(
                CabecalhoType,
                "dtFim",
                dados_lote_rps["date_in_out"].split("T", 1)[0],
            ),
            QtdRPS=self.convert_type_nfselib(CabecalhoType, "QtdRPS", "1"),
        )

    def _nfse_paulistana_discriminacao(self, dados_servico):
        # No v18 o name da linha fiscal e computado como "<display_name do produto>\n
        # <descricao manual>" (ex.: "[753] Consultoria\nConsultoria"). A NFS-e, em
        # paridade com o v14 (onde name era Text puro = so a descricao), usa apenas a
        # descricao: tudo apos a 1a quebra de linha (a 1a linha e o rotulo do produto).
        # Sem quebra de linha (linha so com produto, sem descricao manual) remove apenas
        # o prefixo "[codigo]". O comentario vem de additional_data da LINHA
        # (renderizado a partir de comment_ids); fiscal_additional_data e do documento
        # e nunca e usado.
        descricao = dados_servico["discriminacao"] or ""
        if "\n" in descricao:
            descricao = descricao.split("\n", 1)[1]
        else:
            code = self.fiscal_line_ids[:1].product_id.default_code
            if code and descricao.startswith(f"[{code}]"):
                descricao = descricao[len(f"[{code}]") :]
        descricao = descricao.strip()
        adicional = (
            self.fiscal_line_ids[:1].additional_data or self.fiscal_additional_data
        )
        if adicional:
            descricao += "|{}|".format(adicional.replace("\n", "|"))
        return unidecode(descricao)

    def _serialize_lote_rps(self, dados_lote_rps, dados_servico):
        dados_tomador = self._prepare_dados_tomador()
        gIBSCBS = tpGIBSCBS(
            cClassTrib=self.convert_type_nfselib(
                tpGIBSCBS,
                "cClassTrib",
                self.fiscal_line_ids[:1].tax_classification_id.code,
            )
        )
        trib = tpTrib(gIBSCBS=gIBSCBS)
        valores = tpValores(trib=trib)
        IBSCBS = tpIBSCBS(
            finNFSe=self.convert_type_nfselib(tpIBSCBS, "finNFSe", 0),
            indFinal=self.convert_type_nfselib(tpIBSCBS, "indFinal", 0),
            cIndOp=self.convert_type_nfselib(
                tpIBSCBS,
                "cIndOp",
                self.fiscal_line_ids[:1].operation_indicator_id.code,
            ),
            indDest=self.convert_type_nfselib(tpIBSCBS, "indDest", 1),
            valores=valores,
        )
        return tpRPS(
            Assinatura=self.assinatura_rps(
                dados_lote_rps, dados_servico, dados_tomador
            ),
            ChaveRPS=tpChaveRPS(
                InscricaoPrestador=self.convert_type_nfselib(
                    tpChaveRPS,
                    "InscricaoPrestador",
                    dados_lote_rps["inscricao_municipal"].zfill(8),
                ),
                SerieRPS=self.convert_type_nfselib(
                    tpChaveRPS, "SerieRPS", dados_lote_rps["serie"]
                ),
                NumeroRPS=self.convert_type_nfselib(
                    tpChaveRPS, "NumeroRPS", dados_lote_rps["numero"]
                ),
            ),
            TipoRPS=self._map_type_rps(dados_lote_rps["tipo"]),
            DataEmissao=self.convert_type_nfselib(
                tpRPS, "DataEmissao", dados_lote_rps["data_emissao"].split("T", 1)[0]
            ),
            StatusRPS=self.convert_type_nfselib(tpRPS, "StatusRPS", "N"),
            TributacaoRPS=self.convert_type_nfselib(
                tpRPS,
                "TributacaoRPS",
                self._map_taxation_rps(dados_lote_rps["natureza_operacao"]),
            ),
            # Schema v02 (reforma) define ValorInicialCobrado XOR ValorFinalCobrado
            # (xs:choice): enviar apenas UM. Enviamos ValorFinalCobrado (paridade v14).
            ValorFinalCobrado=self.convert_type_nfselib(
                tpRPS, "ValorFinalCobrado", dados_servico["valor_servicos"]
            ),
            ValorDeducoes=self.convert_type_nfselib(
                tpRPS, "ValorDeducoes", dados_servico["valor_deducoes"]
            ),
            ValorPIS=self.convert_type_nfselib(
                tpRPS, "ValorPIS", dados_servico["valor_pis"]
            ),
            ValorCOFINS=self.convert_type_nfselib(
                tpRPS, "ValorCOFINS", dados_servico["valor_cofins"]
            ),
            ValorINSS=self.convert_type_nfselib(
                tpRPS, "ValorINSS", dados_servico["valor_inss_retido"]
            ),
            ValorIR=self.convert_type_nfselib(
                tpRPS, "ValorIR", dados_servico["valor_ir_retido"]
            ),
            # Manual da Paulistana: ValorCSLL carrega o somatorio das retencoes
            # federais (PIS + COFINS + CSLL retidos), nao o CSLL isolado.
            ValorCSLL=self.convert_type_nfselib(
                tpRPS,
                "ValorCSLL",
                dados_servico["valor_pis_retido"]
                + dados_servico["valor_cofins_retido"]
                + dados_servico["valor_csll_retido"],
            ),
            CodigoServico=self.convert_type_nfselib(
                tpRPS, "CodigoServico", dados_servico["codigo_tributacao_municipio"]
            ),
            # Reforma Tributária — novos campos obrigatórios v3.3.4
            ExigibilidadeSuspensa=self.convert_type_nfselib(
                tpRPS, "ExigibilidadeSuspensa", 0
            ),
            PagamentoParceladoAntecipado=self.convert_type_nfselib(
                tpRPS, "PagamentoParceladoAntecipado", 0
            ),
            NBS=self.convert_type_nfselib(
                tpRPS, "NBS", dados_servico["codigo_nbs_unmasked"]
            ),
            # Schema v02 (reforma) define cLocPrestacao XOR cPaisPrestacao (xs:choice):
            # servico prestado no Brasil usa cLocPrestacao (codigo IBGE do municipio).
            cLocPrestacao=self.convert_type_nfselib(
                tpRPS, "cLocPrestacao", self.partner_id.city_id.ibge_code
            ),
            ValorIPI=self.convert_type_nfselib(tpRPS, "ValorIPI", 0),
            AliquotaServicos=self.convert_type_nfselib(
                tpRPS, "AliquotaServicos", dados_servico["aliquota"]
            ),
            ISSRetido="true"
            if float(dados_servico.get("valor_iss_retido") or 0) > 0
            else "false",
            # FIXME: Hardcoded
            CPFCNPJTomador=self.convert_type_nfselib(
                tpRPS,
                "CPFCNPJTomador",
                tpCPFCNPJNIF(CNPJ=dados_tomador["cnpj"], CPF=dados_tomador["cpf"]),
            ),
            InscricaoMunicipalTomador=self.convert_type_nfselib(
                tpRPS,
                "InscricaoMunicipalTomador",
                dados_tomador["inscricao_municipal"],
            )
            if dados_tomador["codigo_municipio"]
            == int(f"{self.company_id.partner_id.city_id.ibge_code}")
            else None,
            InscricaoEstadualTomador=self.convert_type_nfselib(
                tpRPS, "InscricaoEstadualTomador", dados_tomador["inscricao_estadual"]
            ),
            RazaoSocialTomador=self.convert_type_nfselib(
                tpRPS, "RazaoSocialTomador", dados_tomador["razao_social"]
            ),
            EnderecoTomador=tpEndereco(
                Logradouro=self.convert_type_nfselib(
                    tpEndereco, "Logradouro", dados_tomador["endereco"]
                ),
                NumeroEndereco=self.convert_type_nfselib(
                    tpEndereco, "NumeroEndereco", dados_tomador["numero"]
                ),
                ComplementoEndereco=self.convert_type_nfselib(
                    tpEndereco, "ComplementoEndereco", dados_tomador["complemento"]
                ),
                Bairro=self.convert_type_nfselib(
                    tpEndereco, "Bairro", dados_tomador["bairro"]
                ),
                Cidade=self.convert_type_nfselib(
                    tpEndereco, "Cidade", dados_tomador["codigo_municipio"]
                ),
                UF=self.convert_type_nfselib(tpEndereco, "UF", dados_tomador["uf"]),
                CEP=self.convert_type_nfselib(tpEndereco, "CEP", dados_tomador["cep"]),
            ),
            EmailTomador=self.convert_type_nfselib(
                tpRPS, "EmailTomador", dados_tomador["email"]
            ),
            Discriminacao=self.convert_type_nfselib(
                tpRPS,
                "Discriminacao",
                self._nfse_paulistana_discriminacao(dados_servico),
            ),
            MunicipioPrestacao=self.convert_type_nfselib(
                CabecalhoType,
                "Versao",
                self._map_provision_municipality(
                    dados_lote_rps["natureza_operacao"],
                    dados_servico["codigo_municipio"],
                ),
            ),
            IBSCBS=IBSCBS,
            RetencaoPisCofins=self.convert_type_nfselib(
                tpRPS,
                "RetencaoPisCofins",
                self._map_retencao_pis_cofins(
                    dados_servico["valor_pis_retido"],
                    dados_servico["valor_cofins_retido"],
                    dados_servico["valor_csll_retido"],
                ),
            ),
        )

    def assinatura_rps(self, dados_lote_rps, dados_servico, dados_tomador):
        """Monta os bytes ASCII da assinatura do RPS (pre-Base64).

        Layout da Reforma Tributária: inscrição municipal com 12 dígitos
        (o layout anterior usava 8).
        """
        assinatura = ""

        inscr_mun = misc.punctuation_rm(dados_lote_rps["inscricao_municipal"] or "")
        assinatura += inscr_mun.zfill(12)
        assinatura += (dados_lote_rps["serie"] or "").ljust(5)[:5]
        assinatura += str(dados_lote_rps["numero"]).zfill(12)

        dt_emissao = datetime.strptime(
            dados_lote_rps["data_emissao"], "%Y-%m-%dT%H:%M:%S"
        )
        assinatura += dt_emissao.strftime("%Y%m%d")
        assinatura += self._map_taxation_rps(dados_lote_rps["natureza_operacao"])

        status_rps = dados_lote_rps.get("status_rps") or "N"
        assinatura += status_rps

        assinatura += (
            "S" if float(dados_servico.get("valor_iss_retido") or 0) > 0 else "N"
        )

        valor_inicial_cobrado = dados_servico.get("valor_inicial_cobrado")
        valor_final_cobrado = dados_servico.get("valor_servicos")
        valor_base_assinatura = (
            valor_inicial_cobrado
            if valor_inicial_cobrado is not None
            else valor_final_cobrado
            if valor_final_cobrado is not None
            else dados_servico["valor_servicos"]
        )
        assinatura += f"{float(valor_base_assinatura):.2f}".replace(".", "").zfill(15)

        valor_deducoes = dados_servico.get("valor_deducoes", 0.0)
        assinatura += f"{float(valor_deducoes):.2f}".replace(".", "").zfill(15)

        assinatura += str(dados_servico["codigo_tributacao_municipio"]).zfill(5)

        has_cnpj_tomador = bool(dados_tomador.get("cnpj"))
        assinatura += "2" if has_cnpj_tomador else "1"

        doc_tomador = misc.punctuation_rm(
            dados_tomador.get("cnpj") or dados_tomador.get("cpf") or ""
        )
        assinatura += doc_tomador.zfill(14)

        return assinatura.encode("ascii")

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

    def _map_retencao_pis_cofins(
        self, valor_pis_retido, valor_cofins_retido, valor_csll_retido
    ):
        # NT-007: indicador de retenção de PIS/COFINS/CSLL
        dict_retencao_pis_cofins_csll = {
            (False, False, False): "0",  # PIS/COFINS/CSLL Não Retidos.
            (True, True, True): "3",  # PIS/COFINS/CSLL Retidos.
            (True, True, False): "4",  # PIS/COFINS Retidos, CSLL Não Retido.
            (True, False, False): "5",  # PIS Retido, COFINS/CSLL Não Retidos.
            (False, True, False): "6",  # COFINS Retido, PIS/CSLL Não Retidos.
            (False, True, True): "7",  # PIS Não Retido, COFINS/CSLL Retidos.
            (False, False, True): "8",  # PIS/COFINS Não Retidos, CSLL Retido.
            (True, False, True): "9",  # COFINS Não Retido, PIS/CSLL Retidos.
        }
        pis_retido = float(valor_pis_retido or 0) > 0
        cofins_retido = float(valor_cofins_retido or 0) > 0
        csll_retido = float(valor_csll_retido or 0) > 0
        return dict_retencao_pis_cofins_csll[(pis_retido, cofins_retido, csll_retido)]

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
                                        mensagem_erro += f"{codigo} - {descricao}\n"

                                    vals["edoc_error_message"] = mensagem_erro
                                    vals["status_name"] = _("Procesado com Erro")
                                    vals["status_code"] = 3
                                    record._change_state(SITUACAO_EDOC_REJEITADA)
                record.write(vals)
        return

    def _document_status(self):
        status = super()._document_status()
        for record in self.filtered(filter_oca_nfse).filtered(filter_paulistana):
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
            if isinstance(consulta, dict):
                # erpbrasil.edoc devolve o texto cru do elemento DataEmissaoNFe
                # (xsd:dateTime, ex.: "2020-01-01T10:00:00") e campos Datetime
                # do Odoo so aceitam "%Y-%m-%d %H:%M:%S".
                data_emissao = fields.Datetime.to_datetime(
                    consulta["data_emissao"].replace("T", " ")
                )
                record.write(
                    {
                        "verify_code": consulta["codigo_verificacao"],
                        "document_number": consulta["numero"],
                        "authorization_date": data_emissao,
                    }
                )
                record.authorization_event_id.set_done(
                    status_code=4,
                    response=_("Procesado com Sucesso"),
                    protocol_date=data_emissao,
                    protocol_number=record.authorization_protocol,
                    file_response_xml=processo.retorno,
                )
                status = _("Procesado com Sucesso")
            else:
                # erpbrasil.edoc returns the webservice error message as text
                status = consulta
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
