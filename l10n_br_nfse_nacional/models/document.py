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
from erpbrasil.assinatura.assinatura import Assinatura
from erpbrasil.assinatura.certificado import ArquivoCertificado
from erpbrasil.base.misc import punctuation_rm
from lxml import etree
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
    TclocPrest,
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

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    SITUACAO_EDOC_AUTORIZADA,
    TAX_FRAMEWORK_SIMPLES_ALL,
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
                raise UserError(
                    _(
                        "%(status)s - %(text)s",
                        status=response.status_code,
                        text=response.text,
                    )
                )


def filter_nacional(record):
    return record.company_id.provedor_nfse == "nacional"


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

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
            locPrest=TclocPrest(  # TODO complete
                cLocPrestacao=dados["municipio_prestacao_servico"]
                if dados.get("municipio_prestacao_servico")
                else None,
            ),
            cServ=Tccserv(
                cTribNac=dados["item_lista_servico"].zfill(6),
                # TODO not this one? (should be 3 digits only):
                # cTribMun=dados["codigo_tributacao_municipio"],
                xDescServ=dados["discriminacao"],
                cNBS=self.fiscal_line_ids[0].product_id.nbs_id.code or None,
                # cIntContrib= TODO
            ),
        )

    def _serialize_nacional_dados_tomador(self):
        dados = self._prepare_dados_tomador()
        return TcinfoPessoa(
            CNPJ=dados["cnpj"],
            CPF=dados["cpf"],
            # NIF= TODO
            # cNaoNIF= TODO
            # CAEPF= TODO
            IM=dados["inscricao_municipal"],
            xNome=self.partner_id.legal_name,
            end=Tcendereco(
                endNac=TcenderNac(
                    cMun=dados["codigo_municipio"],
                    # force 8 digits for CEP as per xsd:
                    CEP=str(dados["cep"]).zfill(8),
                ),
                # TODO endExt
                xLgr=dados["endereco"],
                nro=dados["numero"],
                xCpl=dados["complemento"],
                xBairro=dados["bairro"],
            ),
            fone=punctuation_rm(
                self.partner_id.mobile or self.partner_id.phone or ""
            ).replace(" ", ""),
            email=self.partner_id.email,
        )

    def _serialize_nacional_rps(self, dados_lote_rps, dados_servico):
        trib_issqn = self.operation_nature  # TODO "5" and "6" don't match!
        if trib_issqn == "1":
            if self.company_id.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
                trib_nac = None
                tot_trib = TctribTotal(pTotTribSN=dados_servico["aliquota"])
            else:
                trib_nac = TctribNacional(
                    piscofins=TctribOutrosPisCofins(
                        vPis=dados_servico["valor_pis"],
                        vCofins=dados_servico["valor_cofins"],
                    ),
                    vRetCP=dados_servico["valor_inss_retido"],
                    vRetIRRF=dados_servico["valor_ir_retido"],
                    vRetCSLL=dados_servico["valor_csll_retido"],
                )
                tot_trib = TctribTotal(
                    pTotTrib=dados_servico["aliquota"],
                )
                # TODO vTotTrib

        else:
            trib_nac = None
            tot_trib = TctribTotal(
                indTotTrib=0,
            )

        emitente = self.company_id.partner_id
        if emitente.is_company:
            inscr_fed_type = "1"
            id_dps = (
                "DPS"
                + emitente.city_id.ibge_code
                + inscr_fed_type
                + punctuation_rm(emitente.inscr_est).zfill(14)
                + dados_lote_rps["serie"].zfill(5)
                + dados_lote_rps["numero"].zfill(15)
            )
        else:
            inscr_fed_type = "2"  # TODO 3: CAEPF, 4:CNO
            id_dps = (
                "DPS"
                + emitente.city_id.ibge_code
                + inscr_fed_type
                + punctuation_rm(emitente.cnpj_cpf).zfill(14)
                + dados_lote_rps["serie"].zfill(5)
                + dados_lote_rps["numero"].zfill(15)
            )

        return TcinfDps(
            tpAmb=self.nfse_environment,
            Id=id_dps,
            nDPS=dados_lote_rps["numero"],
            serie=dados_lote_rps["serie"],
            dhEmi=fields.Datetime.context_timestamp(
                self, fields.Datetime.from_string(self.document_date)
            ).isoformat("T"),
            verAplic="Odoo OCA",  # TODO sure?
            # TODO dCompet should be the day the service was done
            dCompet=fields.Datetime.from_string(self.document_date).strftime(
                "%Y-%m-%d"
            ),
            tpEmit="1",  # TODO can be 2 or 3
            cLocEmi=self.company_id.partner_id.city_id.ibge_code,
            prest=TcinfoPrestador(
                CNPJ=dados_lote_rps["cnpj"],
                # CPF=  # TODO
                IM=dados_lote_rps["inscricao_municipal"],
                fone=punctuation_rm(
                    self.company_id.partner_id.mobile
                    or self.company_id.partner_id.phone
                    or ""
                ).replace(" ", ""),
                email=self.company_id.partner_id.email,
                regTrib=TcregTrib(
                    opSimpNac=dados_lote_rps["optante_simples_nacional"],
                    regApTribSN="1"
                    if dados_lote_rps["optante_simples_nacional"] == "1"
                    else None,  # TODO complete
                    regEspTrib=dados_lote_rps["regime_especial_tributacao"],
                ),
            ),
            serv=self._serialize_nacional_dados_servico(),
            toma=self._serialize_nacional_dados_tomador(),
            valores=TcinfoValores(
                vServPrest=TcvservPrest(
                    vServ="{:.2f}".format(dados_servico["valor_servicos"]),
                    # vReceb=
                ),
                vDescCondIncond=TcvdescCondIncond(
                    vDescIncond="{:.2f}".format(
                        dados_servico["valor_desconto_incondicionado"]
                    ),
                    # vDescCond=  # TODO
                ),
                vDedRed=TcinfoDedRed("{:.2f}".format(dados_servico["valor_deducoes"])),
                trib=TcinfoTributacao(
                    tribMun=TctribMunicipal(
                        tribISSQN=trib_issqn,
                        # cPaisResult=self.partner_id.country_id.code,
                        # BM=,
                        # exigSusp=,
                        # tpImunidade=,
                        pAliq=dados_servico["aliquota"],
                        tpRetISSQN=dados_servico["iss_retido"],
                    ),
                    tribNac=trib_nac,
                    totTrib=tot_trib,
                ),
            ),
        )

    def serialize_nfse_nacional(self):
        dados_lote_rps = self._prepare_lote_rps()
        dados_servico = self._prepare_dados_servico()
        dps = Dps(
            infDPS=self._serialize_nacional_rps(dados_lote_rps, dados_servico),
            versao="1.00",
        )
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
        if self.filtered(filter_processador_edoc_nfse).filtered(filter_nacional):
            result = super(FiscalDocument, self)._document_export()
        else:
            result = super()._document_export()
        for record in self.filtered(filter_nacional).filtered(filter_nacional):
            edoc = record.serialize()[0]
            processador = record._processador_nfse_nacional()
            edoc_xml = processador.render_edoc_xsdata(edoc, pretty_print=pretty_print)
            edoc_etree = etree.fromstring(edoc_xml.encode())
            certificate = self.env.company._get_br_ecertificate()
            signed_xml = Assinatura(certificate).assina_xml2(
                edoc_etree, edoc.infDPS.Id, False
            )
            if not self.env.context.get("skip_sign"):
                edoc_xml = signed_xml
            event_id = self.event_ids.create_event_save_xml(
                company_id=self.company_id,
                environment=(
                    EVENT_ENV_PROD if self.nfse_environment == "1" else EVENT_ENV_HML
                ),
                event_type="0",
                xml_file=edoc_xml,
                document_id=self,
            )
            _logger.debug(signed_xml)
            record.authorization_event_id = event_id
            record.make_pdf()
        return result

    def _document_status(self):
        # TODO
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_nacional
        ):
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
