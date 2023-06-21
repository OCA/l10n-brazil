# Copyright 2023 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import gzip
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

DANFSE_URL = "https://sefin.nfse.gov.br/sefinnacional"
DFE_URL = "https://adn.nfse.gov.br/contribuinte"
DPS_URL = "https://sefin.nfse.gov.br/sefinnacional"
EVENTOS_URL = "https://sefin.nfse.gov.br/sefinnacional"
NFSE_URL = "https://sefin.nfse.gov.br/sefinnacional"
TAX_URL = "https://sefin.nfse.gov.br/sefinnacional"


_logger = logging.getLogger(__name__)


class NFSeRESTClient(object):
    def __init__(self, tpAmb, certificate):
        self.tpAmb = tpAmb
        self.certificate = certificate

    def render_edoc_xsdata(self, edoc, pretty_print=False):
        """
        Same as render_edoc but compatible with xsdata bindings.
        """
        serializer = XmlSerializer(config=SerializerConfig(pretty_print=pretty_print))
        ns_map = {None: "http://www.sped.fazenda.gov.br/nfse"}
        return serializer.render(obj=edoc, ns_map=ns_map)

    def processar_documento(self, edoc):
        edoc_xml = self.render_edoc_xsdata(edoc)
        compressed_data = gzip.compress(edoc_xml.encode())
        encoded_data = base64.b64encode(compressed_data).decode()
        payload = {"dpsXmlGZipB64": encoded_data}
        return self._post(NFSE_URL + "/nfse", payload)

    def _post(self, url, payload):
        headers = {"Content-Type": "application/json"}
        with ArquivoCertificado(self.certificate, "r") as (key, cert):
            response = requests.post(url, json=payload, headers=headers, verify=False)
            _logger.info("********** RESPONSE TODO REMOVE %s", response.status_code)
            _logger.info("********** RESPONSE TODO REMOVE %s", response.text)
            if response.status_code == 201:
                return response
            else:
                raise UserError(_("%s - %s" % (response.status_code, response.text)))


def filter_nacional(record):
    if record.company_id.provedor_nfse == "nacional":
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
            filter_nacional
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
            #            RazaoSocial? dados["razao_social"] ?
            end=Tcendereco(
                endNac=TcenderNac(
                    cMun=dados["codigo_municipio"],
                    CEP=dados["cep"],
                ),
                # TODO endExt
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

    def _processador_nfse_nacional(self):
        if environ.get("CERT_FILE") and environ.get(
            "CERT_PASSWORD"
        ):  # TODO FIXME only for tests
            cert_bytes = Path(environ["CERT_FILE"]).read_bytes()
        else:
            cert_bytes = None

        certificado = cert.Certificado(
            arquivo=cert_bytes or self.company_id.certificate_nfe_id.file,
            senha=environ.get("CERT_PASSWORD")
            or self.company_id.certificate_nfe_id.password,
        )
        return NFSeRESTClient(tpAmb=self.nfse_environment, certificate=certificado)

    def _document_export(self, pretty_print=True):
        result = super(FiscalDocument, self)._document_export()
        # we skip super the l10n_br_nfase super because we don't use erpbrasil.edoc
        for record in self.filtered(filter_nacional):
            if record.company_id.provedor_nfse:
                edoc = record.serialize()[0]
                processador = record._processador_nfse_nacional()
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
        # TODO
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_nacional
        ):
            processador = record._processador_erpbrasil_nfse()  # TODO
            processo = processador.cancela_documento(
                doc_numero=int(record.document_number)
            )

            status, message = processador.analisa_retorno_cancelamento(processo)

            if not status:
                raise UserError(_(message))

            record.cancel_event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=(
                    EVENT_ENV_PROD if self.nfse_environment == "1" else EVENT_ENV_HML
                ),
                event_type="2",
                xml_file=processo.envio_xml.decode("utf-8"),
                document_id=record,
            )

            return status

    def _document_status(self):
        # TODO
        for record in self.filtered(filter_processador_edoc_nfse):
            processador = record._processador_erpbrasil_nfse()  # TODO
            processo = processador.consulta_nfse_rps(
                rps_number=int(record.rps_number),
                rps_serie=record.document_serie,
                rps_type=int(record.rps_type),
            )

            return _(
                processador.analisa_retorno_consulta(
                    processo,
                    record.document_number,
                    record.company_cnpj_cpf,
                    record.company_legal_name,
                )
            )

    def _eletronic_document_send(self):  # TODO
        super()._eletronic_document_send()
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_nacional
        ):
            processador = record._processador_nfse_nacional()
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
        super()._exec_before_SITUACAO_EDOC_CANCELADA(old_state, new_state)
        return self.cancel_document_nacional()
