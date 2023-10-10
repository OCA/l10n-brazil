# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import gzip
import json
import logging
from datetime import datetime
from os import environ
from pathlib import Path

import requests
from erpbrasil.assinatura import certificado as cert
from erpbrasil.assinatura.certificado import ArquivoCertificado
from nfelib.nfse.bindings.v1_0.dps_v1_00 import Dps
from nfelib.nfse.bindings.v1_0.tipos_complexos_v1_00 import (
    Tccserv,
    Tcendereco,
    TcenderNac,
    TcinfDps,
    TcinfoDedRed,
    TcinfoPessoa,
    TcinfoPrestador,
    TcinfoTributacao,
    TcinfoValores,
    TcregTrib,
    Tcserv,
    TctribMunicipal,
    TctribNacional,
    TctribOutrosPisCofins,
    TctribTotal,
    TcvdescCondIncond,
    TcvservPrest,
)
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    SITUACAO_EDOC_AUTORIZADA,
)
from odoo.addons.l10n_br_fiscal.models.document import Document as FiscalDocument
from odoo.addons.l10n_br_nfse.models.document import filter_processador_edoc_nfse

_logger = logging.getLogger(__name__)

NFSE_URL = {
    "1": 'https://api.focusnfe.com.br',
    "2": 'https://homologacao.focusnfe.com.br'
}

API_ENDPOINT = {
    'envio': '/v2/nfse?ref=',
    'status': '/v2/nfse/',
    'resposta': '/v2/nfse/',
    'cancelamento': '/v2/nfse/',
}

class NFSeFocus(object):
    def __init__(self, tpAmb, token_focusnfe, company):
        self.tpAmb = tpAmb
        self.token_focusnfe = token_focusnfe
        self.company = company

    def render_edoc_xsdata(self, edoc, pretty_print=False):
        """
        Same as render_edoc but compatible with xsdata bindings.
        """
        serializer = XmlSerializer(config=SerializerConfig(pretty_print=pretty_print))
        ns_map = {None: "http://www.sped.fazenda.gov.br/nfse"}
        return serializer.render(obj=edoc, ns_map=ns_map)

    def processar_documento(self, edoc):       
        nfse = {}
        nfse["prestador"] = {}
        nfse["servico"] = {}
        nfse["tomador"] = {}
        nfse["tomador"]["endereco"] = {}

        nfse["razao_social"] = self.company.name
        nfse["data_emissao"] = edoc.infDPS.dhEmi
        nfse["incentivador_cultural"] =  self.company.cultural_sponsor
        nfse["natureza_operacao"] = "1"
        # Verificar esse campo
        nfse["optante_simples_nacional"] = "true"
        nfse["status"] = "1"
        nfse["prestador"]["cnpj"] = edoc.infDPS.prest.CNPJ
        nfse["prestador"]["inscricao_municipal"] = edoc.infDPS.prest.IM
        nfse["prestador"]["codigo_municipio"] = self.company.city_id.ibge_code
        # Verificar esses campos
        nfse["servico"]["aliquota"] = "2.92"
        nfse["servico"]["base_calculo"] = "1.00"
        nfse["servico"]["discriminacao"] = "SERVICOS E MAO DE OBRA"
        nfse["servico"]["iss_retido"] = "0"
        nfse["servico"]["item_lista_servico"] = "1412"
        nfse["servico"]["valor_iss"] = "11.68"
        nfse["servico"]["valor_liquido"] = "1.00"
        nfse["servico"]["valor_servicos"] = "1.00"
        nfse["tomador"]["cnpj"] = edoc.infDPS.toma.CNPJ
        nfse["tomador"]["razao_social"] = "Parkinson da silva coelho JR"
        nfse["tomador"]["endereco"]["bairro"] = edoc.infDPS.toma.end.xBairro
        nfse["tomador"]["endereco"]["cep"] = edoc.infDPS.toma.end.endNac.CEP
        nfse["tomador"]["endereco"]["codigo_municipio"] = edoc.infDPS.toma.end.endNac.cMun
        nfse["tomador"]["endereco"]["logradouro"] = edoc.infDPS.toma.end.xLgr
        nfse["tomador"]["endereco"]["numero"] = edoc.infDPS.toma.end.nro
        nfse["tomador"]["endereco"]["uf"] = "MG"
        
        payload = json.dumps(nfse)
        ref = {"ref":"12345"}
        return self._post(NFSE_URL[self.tpAmb] + API_ENDPOINT['envio'], payload, ref)

    def _post(self, url, payload, ref):
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, params=ref, data=payload, auth=(self.token_focusnfe,""))

        if response.status_code == 201 or response.status_code == 200 or response.status_code == 202:
            return response
        else:
            raise UserError(_("%s - %s" % (response.status_code, response.text)))

def filter_focusnfe(record):
    if record.company_id.provedor_nfse == "focusnfe":
        return True
    return False

class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def convert_type_nfselib(self, class_object, object_filed, value):
        if value is None:
            return value

        value_type = ""
        for field in class_object().member_data_items_:
            if field.name == object_filed:
                value_type = field.child_attrs.get("type", "").replace("xsd:", "")
                break

        if value_type in ("int", "byte", "nonNegativeInteger"):
            return int(value)
        elif value_type == "decimal":
            return float(value)
        elif value_type == "string":
            return str(value)
        else:
            return value

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe
        ):
            edocs.append(record.serialize_nfse_nacional())
        return edocs

    def _serialize_nacional_dados_servico(self):
        self.fiscal_line_ids.ensure_one()
        dados = self._prepare_dados_servico()
        return Tcserv(
            #           locPrest=  # TODO
            cServ=Tccserv(
                # cTribNac= TODO ?
                # dados["codigo_cnae"] TODO ?
                # cNBS= TODO?
                #                cTribMun=  # TODO
                cTribMun=dados["codigo_tributacao_municipio"],
                xDescServ=dados["discriminacao"],
            )
            #   TODO ?
            #   ItemListaServico=self.convert_type_nfselib(
            #       tcDadosServico, "ItemListaServico", dados["item_lista_servico"]
            #   ),
            #   CodigoMunicipio=self.convert_type_nfselib(
            #       tcDadosServico, "CodigoMunicipio", dados["codigo_municipio"]
            #   ),
        )

    def _serialize_nacional_dados_tomador(self):
        dados = self._prepare_dados_tomador()
        return TcinfoPessoa(
            CNPJ=dados["cnpj"],
            CPF=dados["cpf"],
            IM=dados["inscricao_municipal"],
            end=Tcendereco(
                endNac=TcenderNac(
                    cMun=dados["codigo_municipio"],
                    CEP=dados["cep"],
                ),
                xLgr=dados["endereco"],
                nro=dados["numero"],
                xCpl=dados["complemento"],
                xBairro=dados["bairro"],
            ),
        )


    def _serialize_nacional_rps(self, dados_lote_rps, dados_servico):
        return TcinfDps(
            tpAmb=self.nfse_environment,
            Id=dados_lote_rps["id"],
            nDPS=dados_lote_rps["numero"],
            serie=dados_lote_rps["serie"],
            # tipo=dados["tipo"],
            dhEmi=dados_lote_rps["date_in_out"],  # NOTE convert?
            verAplic="Odoo OCA",  # TODO sure?
            #            dCompet=  # TODO
            # TODO ?
            #   NaturezaOperacao=self.convert_type_nfselib(
            #       tcInfRps, "NaturezaOperacao", dados["natureza_operacao"]
            #   ),
            #   IncentivadorCultural=self.convert_type_nfselib(
            #       tcInfRps, "IncentivadorCultural", dados["incentivador_cultural"]
            #   ),
            #   Status=self.convert_type_nfselib(tcInfRps, "Status", dados["status"]),
            #   RpsSubstituido=self.convert_type_nfselib(
            #       tcInfRps, "RpsSubstituido", dados["rps_substitiuido"]
            #   ),
            prest=TcinfoPrestador(
                CNPJ=dados_lote_rps["cnpj"],
                #                CPF=  # TODO
                IM=dados_lote_rps["inscricao_municipal"],
                regTrib=TcregTrib(
                    opSimpNac=dados_lote_rps["optante_simples_nacional"],
                    #                    regApTribSN=  # TODO
                    regEspTrib=dados_lote_rps["regime_especial_tributacao"],
                ),
            ),
            serv=self._serialize_nacional_dados_servico(),
            toma=self._serialize_nacional_dados_tomador(),
            valores=TcinfoValores(
                vServPrest=TcvservPrest(
                    vServ=dados_servico["valor_servicos"],
                    #                        vReceb=
                ),
                vDescCondIncond=TcvdescCondIncond(
                    vDescIncond=dados_servico["valor_desconto_incondicionado"],
                    #                    vDescCond=  # TODO
                ),
                # TODO
                #                    ValorServicos=self.convert_type_nfselib(
                #                        tcValores, "ValorServicos", dados["valor_servicos"]
                #                    ),
                vDedRed=TcinfoDedRed(vDR=dados_servico["valor_deducoes"]),
                #                    ValorDeducoes=self.convert_type_nfselib(
                #                        tcValores, "ValorDeducoes", dados["valor_deducoes"]
                #                    ),
                trib=TcinfoTributacao(
                    tribMun=TctribMunicipal(
                        #                        tribISSQN=  # TODO
                        #                        tpRetISSQN=  # TODO
                    ),
                    tribNac=TctribNacional(
                        piscofins=TctribOutrosPisCofins(
                            vPis=dados_servico["valor_pis"],
                            vCofins=dados_servico["valor_cofins"],
                        ),
                        #                        vRetCP=  # TODO
                        #                        vRetIRRF =dados_servico["valor_ir"]
                        vRetCSLL=dados_servico["valor_csll"],
                    ),
                    totTrib=TctribTotal(pTotTribSN=dados_servico["aliquota"]),
                )
                # TODO
                #   ValorInss=self.convert_type_nfselib(
                #       tcValores, "ValorInss", dados["valor_inss"]
                #   ),
                #   IssRetido=self.convert_type_nfselib(
                #       tcValores, "IssRetido", dados["iss_retido"]
                #   ),
                #   ValorIss=self.convert_type_nfselib(
                #       tcValores, "ValorIss", dados["valor_iss"]
                #   ),
                #   ValorIssRetido=self.convert_type_nfselib(
                #       tcValores, "ValorIssRetido", dados["valor_iss_retido"]
                #   ),
                #   OutrasRetencoes=self.convert_type_nfselib(
                #       tcValores, "OutrasRetencoes", dados["outras_retencoes"]
                #   ),
                #   BaseCalculo=self.convert_type_nfselib(
                #       tcValores, "BaseCalculo", dados["base_calculo"]
                #   ),
                #   ValorLiquidoNfse=self.convert_type_nfselib(
                #       tcValores, "ValorLiquidoNfse", dados["valor_liquido_nfse"]
                #   ),
                # interm=TcinfoPessoa()  # FIXME dados["intermediario_servico"]
                # ConstrucaoCivil=self.convert_type_nfselib(  # TODO
                #    tcInfRps, "ConstrucaoCivil", dados["construcao_civil"]
                # ),
            ),
        )

    def serialize_nfse_nacional(self):
        #        lote_rps = EnviarLoteRpsEnvio(LoteRps=self._serialize_nacional_lote_rps())
        dados_lote_rps = self._prepare_lote_rps()
        dados_servico = self._prepare_dados_servico()
        dps = Dps(infDPS=self._serialize_nacional_rps(dados_lote_rps, dados_servico))
        return dps

    def _processador_nfse_focus(self):
        return NFSeFocus(tpAmb=self.nfse_environment, token_focusnfe=self.company_id.token_focusnfe, company=self.company_id)

    def _document_export(self, pretty_print=True):
        result = super(FiscalDocument, self)._document_export()
        # we skip super the l10n_br_nfase super because we don't use erpbrasil.edoc
        for record in self.filtered(filter_focusnfe):
            if record.company_id.provedor_nfse:
                edoc = record.serialize()[0]
                processador = record._processador_nfse_focus()
                xml_file = processador.render_edoc_xsdata(
                    edoc, pretty_print=pretty_print
                )
                event_id = self.event_ids.create_event_save_xml(
                    company_id=self.company_id,
                    environment=(
                        EVENT_ENV_PROD
                        if self.nfse_environment == "1"
                        else EVENT_ENV_HML
                    ),
                    event_type="0",
                    xml_file=xml_file,
                    document_id=self,
                )
                _logger.debug(xml_file)
                record.authorization_event_id = event_id
                record.make_pdf()
        return result


    def cancel_document_nacional(self):
        pass
        # # TODO
        # for record in self.filtered(filter_processador_edoc_nfse).filtered(
        #     filter_focusnfe
        # ):
        #     processador = record._processador_erpbrasil_nfse()  # TODO
        #     processo = processador.cancela_documento(
        #         doc_numero=int(record.document_number)
        #     )

        #     status, message = processador.analisa_retorno_cancelamento(processo)

        #     if not status:
        #         raise UserError(_(message))

        #     record.cancel_event_id = record.event_ids.create_event_save_xml(
        #         company_id=record.company_id,
        #         environment=(
        #             EVENT_ENV_PROD if self.nfse_environment == "1" else EVENT_ENV_HML
        #         ),
        #         event_type="2",
        #         xml_file=processo.envio_xml.decode("utf-8"),
        #         document_id=record,
        #     )

        #     return status

    def _document_status(self):
        pass
        # # TODO
        # for record in self.filtered(filter_processador_edoc_nfse):
        #     processador = record._processador_erpbrasil_nfse()  # TODO
        #     processo = processador.consulta_nfse_rps(
        #         rps_number=int(record.rps_number),
        #         rps_serie=record.document_serie,
        #         rps_type=int(record.rps_type),
        #     )

        #     return _(
        #         processador.analisa_retorno_consulta(
        #             processo,
        #             record.document_number,
        #             record.company_cnpj_cpf,
        #             record.company_legal_name,
        #         )
        #     )

    def _eletronic_document_send(self):  # TODO
        super()._eletronic_document_send()
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe
        ):
            processador = record._processador_nfse_focus()
            for edoc in record.serialize():
                response = processador.processar_documento(edoc)
                json = response.json()
                vals = {
                    "document_number": json["idDps"],
                    "authorization_date": json["dataHoraProcessamento"],
                }
                # TODO?  vals["verify_code"] = comp.Nfse.InfNfse.CodigoVerificacao

                decoded_data = base64.b64decode(json["nfseXmlGZipB64"])
                decompressed_data = gzip.decompress(decoded_data)
                nfse_xml = decompressed_data.decode()
                record.authorization_event_id.set_done(
                    status_code=response.status_code,
                    response="FIXME não tem?",  # FIXME
                    protocol_date=datetime.strptime(
                        vals["authorization_date"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    protocol_number="FIXME não tem",  # FIXME
                    file_response_xml=nfse_xml,
                )
                # TODO is it normal to do that in a record.serialize loop?
                record._change_state(SITUACAO_EDOC_AUTORIZADA)

    def _exec_before_SITUACAO_EDOC_CANCELADA(self, old_state, new_state):
        pass
        # super()._exec_before_SITUACAO_EDOC_CANCELADA(old_state, new_state)
        # return self.cancel_document_nacional()


    # def _serialize_focusnfe_dados_servico(self):
    #     self.fiscal_line_ids.ensure_one()
    #     dados = self._prepare_dados_servico()
    #     res = {
    #         "valor_servicos": dados["valor_servicos"],
    #         "valor_deducoes": dados["valor_deducoes"],
    #         "valor_pis": dados["valor_pis"],
    #         "valor_cofins": dados["valor_cofins"],
    #         "valor_inss": dados["valor_inss"],
    #         "valor_ir": dados["valor_ir"],
    #         "valor_csll": dados["valor_csll"],
    #         "iss_retido": dados["iss_retido"],
    #         "valor_iss": dados["valor_iss"],
    #         "valor_iss_retido": dados["valor_iss_retido"],
    #         "outras_retencoes": dados["outras_retencoes"],
    #         "base_calculo": dados["base_calculo"],
    #         "aliquota": dados["aliquota"],
    #         "desconto_incondicionado": "",
    #         "desconto_condicionado": "",
    #         "item_lista_servico": dados["item_lista_servico"],
    #         "codigo_cnae": dados["codigo_cnae"],
    #         "codigo_tributario_municipio": "",
    #         "discriminacao": dados["discriminacao"],
    #         "codigo_municipio": dados["codigo_municipio"],
    #         "percentual_total_tributos": "",
    #         "fonte_total_tributos": "",
    #     }
    #     return res

    # def _serialize_focusnfe_dados_tomador(self):
    #     dados = self._prepare_dados_tomador()
    #     res = {
    #         "cpf": dados["cpf"],
    #         "cnpj": dados["cnpj"],
    #         "inscricao_municipal": dados["inscricao_municipal"],
    #         "razao_social": dados["razao_social"],
    #         "endereco": {
    #             "logradouro": dados["endereco"],
    #             "numero": dados["numero"],
    #             "complemento": dados["complemento"],
    #             "bairro": dados["bairro"],
    #             "codigo_municipio": dados["codigo_municipio"],
    #             "uf": dados["uf"],
    #             "cep": dados["cep"],
    #         },
    #     }

    #     return res

    # def _serialize_focusnfe_lote_rps(self):
    #     dados = self._prepare_lote_rps()
    #     res = {
    #         "cnpj": dados["cnpj"],
    #         "inscricao_municipal": dados["inscricao_municipal"],
    #         "quantidade_rps": 1,
    #         "lista_rps": [self._serialize_focusnfe_rps(dados)],
    #     }
    #     return res

    # def _serialize_focusnfe_rps(self, dados):
    #     res = {
    #       "data_emissao": dados["date_in_out"],
    #         "natureza_operacao": dados["natureza_operacao"],
    #         "regime_especial_tributacao": dados["regime_especial_tributacao"],
    #         "optante_simples_nacional": dados["optante_simples_nacional"],
    #         "incentivador_cultural": dados["incentivador_cultural"],
    #         "codigo_obra": dados["construcao_civil"],
    #         "art": "",
    #         "numero_rps_substituido": dados["numero"],
    #         "serie_rps_substituido": dados["serie"],
    #         "tipo_rps_substituido": dados["tipo"],
    #         "servico": self._serialize_focusnfe_dados_servico(),
    #         "prestador": {
    #             "cnpj": dados["cnpj"],
    #             "inscricao_municipal": dados["inscricao_municipal"],
    #             "codigo_municipio": self._serialize_focusnfe_dados_servico()["codigo_municipio"],
    #         },
    #         "tomador": self._serialize_focusnfe_dados_tomador(),
    #         "intermediario": dados["intermediario_servico"],
    #     }

    #     return res

    # def serialize_focusnfe(self):
    #     lote_rps = self._serialize_focusnfe_lote_rps()
    #     return lote_rps

    # # def _eletronic_document_send(self):
    # # super()._eletronic_document_send()
    # # for record in self.filtered(filter_oca_nfse).filtered(filter_focusnfe):
    # # protocolo = record.authorization_protocol
    # # vals = dict()

    # def view_xml(self):
    #     self.ensure_one()
    #     xml_file = self.authorization_file_id or self.send_file_id
    #     if not xml_file:
    #         self._document_export()
    #         xml_file = self.authorization_file_id or self.send_file_id
    #     if not xml_file:
    #         raise UserError(_("No XML file generated!"))
    #     return self._target_new_tab(xml_file)

    # def _eletronic_document_send(self):
    #     super()._eletronic_document_send()

    # def _processador_focus_nfse(self):
    #     certificado  = cert.Certificado(
    #         arquivo=self.company_id.certificate_nfe_id.file,
    #         senha=self.company_id.certificate_nfe_id.password,
    #     )
    #     session = Session()
    #     session.verify = False
    #     # transmissao = TransmissaoSOAP(certificado, session)

    # def _generatejson_to_string_etree(self, json_file):
    #     xml = dicttoxml(json_file, custom_root='EnviarLoteRpsEnvio', attr_type=False)
    #     return str(xml, 'UTF-8')

    # def _document_export(self, pretty_print=True):
    #     # result = super(Document, self)._document_export()
    #     for record in self.filtered(filter_processador_edoc_nfse):
    #         if self.company_id.provedor_nfse == "focusnfe":
    #             # processador = record._processador_focus_nfse()
    #             json_file = record._serialize_focusnfe_lote_rps()
    #             xml_file = record._generatejson_to_string_etree(json_file)
    #             event_id = self.event_ids.create_event_save_xml(
    #                 company_id=self.company_id,
    #                 environment=(
    #                     EVENT_ENV_PROD
    #                     if self.nfse_environment == "1"
    #                     else EVENT_ENV_HML
    #                 ),
    #                 event_type="0",
    #                 xml_file=xml_file,
    #                 document_id=self,
    #             )
    #             record.make_pdf()
    #             result = xml_file
    #         else:
    #             result = super(Document, self)._document_export()
    #     return result
