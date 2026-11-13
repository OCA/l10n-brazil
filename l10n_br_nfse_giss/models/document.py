# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime
from decimal import Decimal

import pytz
from erpbrasil.base import misc
from erpbrasil.transmissao import TransmissaoSOAP
from lxml import etree
from requests import Session
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.models.datatype import XmlDate

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_REJEITADA,
)
from odoo.addons.l10n_br_nfse.models.document import filter_processador_edoc_nfse

from ..constants import COUNTRY_ISO_NUMERIC

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.edoc.provedores.giss import (
        CANCELAMENTO_ERRO_EMISSAO,
        VERSAO,
        Giss,
    )
    from nfselib.giss.v2_04 import enviar_lote_rps_envio_v2_04 as envio
    from nfselib.giss.v2_04 import tipos_v2_04 as tipos
except ImportError:  # pragma: no cover
    _logger.debug("erpbrasil.edoc with the Giss provider or nfselib.giss missing")

TZ_BR = pytz.timezone("America/Sao_Paulo")
CITY_ABROAD = 9999999
NFSE_GISS_CANCEL_CODES = [
    ("1", "1 - Erro na emissão"),
    ("2", "2 - Serviço não prestado"),
    ("4", "4 - Duplicidade da nota"),
]
# tpRetPisCofins by what is withheld: (PIS, COFINS, CSLL). The codes 1 and 2
# of the older layout are no longer accepted by the webservice.
PIS_COFINS_CSLL_WITHHOLDING = {
    (False, False, False): "0",
    (True, True, True): "3",
    (True, True, False): "4",
    (True, False, False): "5",
    (False, True, False): "6",
    (False, True, True): "7",
    (False, False, True): "8",
    (True, False, True): "9",
}


def filter_giss(record):
    return record.company_id.provedor_nfse == "giss"


def _decimal(value, digits=2):
    return Decimal(str(round(value or 0.0, digits))).quantize(Decimal(10) ** -digits)


def _optional(value, digits=2):
    return _decimal(value, digits) if value else None


class GissProcessor:
    """What l10n_br_nfse expects from the edoc processor, for a xsdata binding.

    The base module exports the XML of the RPS through the processor it gets
    from ``_processador_erpbrasil_nfse``, written for generateDS bindings and
    for the city factory of erpbrasil.edoc. The Giss provider is neither: it
    takes the XML ready.
    """

    def __init__(self, provider):
        self.provider = provider

    def _generateds_to_string_etree(self, edoc, pretty_print=False):
        config = SerializerConfig(indent="  " if pretty_print else None)
        xml = XmlSerializer(config=config).render(edoc)
        return xml, etree.fromstring(xml.encode("utf-8"))


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    is_nfse_giss = fields.Boolean(compute="_compute_is_nfse_giss")
    nfse_giss_national_key = fields.Char(
        string="NFS-e National Key",
        copy=False,
        readonly=True,
        help="Key of the NFS-e in the national environment (ADN), returned by "
        "the city hall with the authorized NFS-e.",
    )
    nfse_giss_cancel_code = fields.Selection(
        selection=NFSE_GISS_CANCEL_CODES,
        string="Cancellation Reason (GissOnline)",
        default="1",
        copy=False,
    )

    @api.depends("company_id.provedor_nfse", "document_type_id")
    def _compute_is_nfse_giss(self):
        giss = self.filtered(filter_processador_edoc_nfse).filtered(filter_giss)
        giss.is_nfse_giss = True
        (self - giss).is_nfse_giss = False

    # -------------------------------------------------------------------------
    # Provider
    # -------------------------------------------------------------------------

    def _giss_provider(self, session=None):
        self.ensure_one()
        company = self.company_id
        transmissao = TransmissaoSOAP(company._get_br_ecertificate(), Session())
        return Giss(
            transmissao=transmissao,
            ambiente=self.nfse_environment,
            cidade_ibge=int(company.partner_id.city_id.ibge_code),
            cnpj_prestador=misc.punctuation_rm(company.partner_id.vat),
            im_prestador=misc.punctuation_rm(company.partner_id.l10n_br_im_code or ""),
            host=company.nfse_giss_host or None,
            session=session,
            verify=company.nfse_ssl_verify,
        )

    def _processador_erpbrasil_nfse(self):
        if self.filtered(filter_giss):
            return GissProcessor(self._giss_provider())
        return super()._processador_erpbrasil_nfse()

    # -------------------------------------------------------------------------
    # RPS
    # -------------------------------------------------------------------------

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_processador_edoc_nfse).filtered(filter_giss):
            edocs.append(record._serialize_nfse_giss())
        return edocs

    def _serialize_nfse_giss(self):
        self.ensure_one()
        lote = self._prepare_lote_rps()
        prestador = self._giss_prestador(lote)
        numero = int(lote["numero"])
        declaracao = tipos.TcInfDeclaracaoPrestacaoServico(
            id=f"rps{numero}",
            rps=tipos.TcInfRps(
                identificacao_rps=tipos.TcIdentificacaoRps(
                    numero=numero,
                    serie=lote["serie"],
                    tipo=lote["tipo"],
                ),
                data_emissao=XmlDate.from_string(lote["data_emissao"][:10]),
                status=lote["status"],
            ),
            competencia=XmlDate.from_string(lote["date_in_out"][:10]),
            servico=self._giss_servico(),
            prestador=prestador,
            tomador_servico=self._giss_tomador(),
            regime_especial_tributacao=lote["regime_especial_tributacao"] or None,
            optante_simples_nacional=lote["optante_simples_nacional"],
            incentivo_fiscal=lote["incentivador_cultural"],
            informacoes_complementares=(
                (self.customer_additional_data or "")[:2000] or None
            ),
        )
        return envio.EnviarLoteRpsEnvio(
            lote_rps=tipos.TcLoteRps(
                id=f"lote{numero}",
                versao=VERSAO,
                numero_lote=numero,
                prestador=prestador,
                quantidade_rps=1,
                lista_rps=tipos.TcLoteRps.ListaRps(
                    rps=[
                        tipos.TcDeclaracaoPrestacaoServico(
                            inf_declaracao_prestacao_servico=declaracao
                        )
                    ]
                ),
            )
        )

    def _giss_prestador(self, lote):
        return tipos.TcIdentificacaoPessoaEmpresa(
            cpf_cnpj=tipos.TcCpfCnpj(cnpj=lote["cnpj"]),
            inscricao_municipal=lote["inscricao_municipal"],
        )

    def _giss_servico(self):
        self.ensure_one()
        dados = self._prepare_dados_servico()
        line = self.fiscal_line_ids[:1]
        retido = dados["iss_retido"] == "1"
        municipio = int(
            dados["municipio_prestacao_servico"] or dados["codigo_municipio"]
        )
        # the export of a service is chosen on the line, never inferred from
        # the customer: it goes to the city abroad, in the country of the
        # customer, with the foreign trade group
        eligibility = line.issqn_eligibility or "1"
        export = eligibility == "4"
        valores = tipos.TcValoresDeclaracaoServico(
            valor_servicos=_decimal(dados["valor_servicos"]),
            valor_deducoes=_optional(dados["valor_deducoes"]),
            # the ABRASF value tags of the federal taxes are the amounts withheld
            valor_pis=_optional(dados["valor_pis_retido"]),
            valor_cofins=_optional(dados["valor_cofins_retido"]),
            valor_inss=_optional(dados["valor_inss_retido"]),
            valor_ir=_optional(dados["valor_ir_retido"]),
            valor_csll=_optional(dados["valor_csll_retido"]),
            valor_iss=_optional(
                dados["valor_iss_retido"] if retido else dados["valor_iss"]
            ),
            # the rate goes as a fraction (5% = 0.0500) and comes back in percent
            aliquota=_optional(dados["aliquota"], 4),
            desconto_incondicionado=_optional(dados["valor_desconto_incondicionado"]),
            trib=self._giss_trib(dados),
            ibscbs=self._giss_ibscbs(dados, municipio),
        )
        return tipos.TcDadosServico(
            valores=valores,
            iss_retido=dados["iss_retido"],
            responsavel_retencao="1" if retido else None,
            # the item goes with the leading zero (01.04) and comes back as 1.04
            item_lista_servico=tipos.TsItemListaServico(
                (line.service_type_id.code or "").zfill(5)
            ),
            codigo_cnae=int(dados["codigo_cnae"]) if dados["codigo_cnae"] else None,
            codigo_tributacao_municipio=dados["codigo_tributacao_municipio"],
            # 9 digits on the way in, dotted on the way back
            codigo_nbs=dados["codigo_nbs_unmasked"] or None,
            discriminacao=self._giss_discriminacao(),
            codigo_municipio=CITY_ABROAD if export else municipio,
            codigo_pais=self._giss_country_code(
                (self.partner_id if export else self.company_id).country_id
            ),
            exigibilidade_iss=eligibility,
            # an export too goes with the city of the provider (E310 without it)
            municipio_incidencia=municipio if eligibility in ("1", "4") else None,
            com_ext=self._giss_com_ext(dados) if export else None,
        )

    def _giss_discriminacao(self):
        """Description of every line, one per row (2000 characters at most).

        The RPS declares a single service with the values of all the lines, so
        the description lists them all, not only the first one.
        """
        return "\n".join(
            line.name for line in self.fiscal_line_ids if line.product_id and line.name
        )[:2000]

    def _giss_trib(self, dados):
        """Federal taxes and the approximate tax burden (group ``trib``)."""
        line = self.fiscal_line_ids[:1]
        pis_cofins = None
        if dados["situacao_tributaria_pis"]:
            withheld = (
                bool(dados["valor_pis_retido"]),
                bool(dados["valor_cofins_retido"]),
                bool(dados["valor_csll_retido"]),
            )
            pis_cofins = tipos.TctribOutrosPisCofins(
                cst=tipos.TstipoCst(dados["situacao_tributaria_pis"]),
                v_bcpis_cofins=_optional(
                    dados["base_calculo_pis"] or dados["base_calculo_cofins"]
                ),
                p_aliq_pis=_optional(dados["aliquota_pis"]),
                p_aliq_cofins=_optional(dados["aliquota_cofins"]),
                v_pis=_optional(dados["valor_pis"]),
                v_cofins=_optional(dados["valor_cofins"]),
                tp_ret_pis_cofins=tipos.TstipoRetPiscofins(
                    PIS_COFINS_CSLL_WITHHOLDING[withheld]
                ),
            )
        burden = line._nfse_approximate_tax_burden()
        if not burden["simples"]:
            total = tipos.TctribTotal(
                p_tot_trib=tipos.TctribTotalPercent(
                    p_tot_trib_fed=_decimal(burden["federal_percent"]),
                    p_tot_trib_est=_decimal(burden["state_percent"]),
                    p_tot_trib_mun=_decimal(burden["city_percent"]),
                )
            )
        elif burden["simples_percent"]:
            total = tipos.TctribTotal(p_tot_trib_sn=_decimal(burden["simples_percent"]))
        else:
            total = tipos.TctribTotal(ind_tot_trib=tipos.TstipoIndTotTrib("0"))
        return tipos.TcinfoTributacao(
            trib_fed=tipos.TctribFederal(piscofins=pis_cofins) if pis_cofins else None,
            tot_trib=total,
        )

    def _giss_ibscbs(self, dados, municipio):
        """IBS/CBS group, when the line carries the data of the tax reform."""
        if not self._nfse_export_ibscbs():
            return None
        line = self._nfse_ibscbs_line()
        return tipos.TcrtcinfoIbscbs(
            fin_nfse=tipos.TsrtcfinNfse("0"),
            ind_final=tipos.TsrtcindFinal("1" if self.ind_final == "1" else "0"),
            c_ind_op=line.operation_indicator_id.code,
            ind_dest=tipos.TsrtcindDest("0"),
            valores=tipos.TcrtcinfoValoresIbscbs(
                trib=tipos.TcrtcinfoTributosIbscbs(
                    g_ibscbs=tipos.TcrtcinfoTributosSitClas(
                        cst=line.ibs_cst_id.code or line.cbs_cst_id.code,
                        c_class_trib=line.tax_classification_id.code,
                    )
                ),
                c_localidade_incid=str(municipio).zfill(7),
                p_redutor=_decimal(0),
                # until 2026 the base leaves out the ISS, PIS and COFINS
                v_bc=_decimal(
                    dados["valor_servicos"]
                    - (dados["valor_desconto_incondicionado"] or 0.0)
                    - (dados["valor_iss"] or 0.0)
                    - (dados["valor_pis"] or 0.0)
                    - (dados["valor_cofins"] or 0.0)
                ),
            ),
        )

    def _giss_com_ext(self, dados):
        """Foreign trade group (``comExt``) of an export invoiced in a foreign
        currency; an export invoiced in reais goes without it."""
        foreign = dados.get("comercio_exterior")
        if not foreign:
            return None
        if not foreign["codigo_moeda"]:
            raise UserError(
                self.env._(
                    "NFS-e GissOnline: the currency %(currency)s has no BACEN code.",
                    currency=foreign["moeda_original"],
                )
            )
        return tipos.TccomExterior(
            md_prestacao=tipos.TsmodoPrestacao(foreign["modo_prestacao"]),
            vinc_prest=tipos.TsvincPrest(foreign["vinculo_negocio"]),
            # BACEN code, as the XSD asks; the authorized NFS-e shows "USD",
            # but the answer reformats the values (see the item and the rate)
            tp_moeda=foreign["codigo_moeda"],
            v_serv_moeda=_decimal(foreign["valor_servico_moeda_original"]),
            mec_afcomex_p=tipos.TsmecAfcomExPrest(foreign["mecanismo_prestador"]),
            mec_afcomex_t=tipos.TsmecAfcomExToma(foreign["mecanismo_tomador"]),
            mov_temp_bens=tipos.TsmovTempBens("1"),
            mdic=tipos.TsenvMdic("0"),
        )

    def _giss_country_code(self, country):
        code = COUNTRY_ISO_NUMERIC.get(country.code or "")
        if not code:
            raise UserError(
                self.env._(
                    "NFS-e GissOnline: %(partner)s has no country with an ISO "
                    "3166 numeric code.",
                    partner=self.partner_id.display_name,
                )
            )
        return code.zfill(4)

    def _giss_tomador(self):
        self.ensure_one()
        dados = self._prepare_dados_tomador()
        contato = tipos.TcContato(email=[dados["email"]]) if dados["email"] else None
        if dados["uf"] == "EX":
            return tipos.TcDadosTomador(
                nif_tomador=(dados["nif"] or "").strip()[:40] or None,
                razao_social=dados["razao_social"],
                endereco_exterior=self._giss_endereco_exterior(dados),
                contato=contato,
            )
        identificacao = None
        if dados["cnpj"] or dados["cpf"]:
            identificacao = tipos.TcIdentificacaoPessoaEmpresa(
                cpf_cnpj=tipos.TcCpfCnpj(cnpj=dados["cnpj"], cpf=dados["cpf"]),
                inscricao_municipal=dados["inscricao_municipal"] or None,
            )
        endereco = tipos.TcEndereco(
            endereco=dados["endereco"],
            numero=dados["numero"] or "S/N",
            complemento=dados["complemento"],
            bairro=dados["bairro"],
            codigo_municipio=dados["codigo_municipio"],
            uf=tipos.TsUf(dados["uf"]),
            cep=dados["cep"],
        )
        return tipos.TcDadosTomador(
            identificacao_tomador=identificacao,
            razao_social=dados["razao_social"],
            endereco=endereco,
            contato=contato,
        )

    def _giss_endereco_exterior(self, dados):
        partner = self.partner_id
        cidade = dados["descricao_municipio"][:60]
        return tipos.TcEnderecoExterior(
            codigo_pais=self._giss_country_code(partner.country_id),
            endereco_completo_exterior=(
                ", ".join(filter(None, [partner.street, partner.street2])) or cidade
            )[:255],
            # mandatory: an address without a postal code goes with zeros
            c_end_post=(partner.zip or "").strip()[:11] or "0000",
            x_cidade=cidade,
            x_est_prov_reg=(partner.state_id.name or "EXTERIOR")[:60],
        )

    # -------------------------------------------------------------------------
    # Transmission
    # -------------------------------------------------------------------------

    def _giss_event_environment(self):
        return EVENT_ENV_PROD if self.nfse_environment == "1" else EVENT_ENV_HML

    @staticmethod
    def _giss_datetime(value):
        """The city hall answers in Brasilia time, without the offset."""
        if not value:
            return False
        local = datetime.fromisoformat(value[:19])
        return TZ_BR.localize(local).astimezone(pytz.utc).replace(tzinfo=None)

    def _giss_authorize(self, retorno):
        """Record the NFS-e the city hall returned for this RPS."""
        self.ensure_one()
        nfse = next(
            (n for n in retorno.nfses if n.numero_rps == str(int(self.rps_number))),
            retorno.nfses[0],
        )
        authorization_date = self._giss_datetime(nfse.data_emissao)
        self.write(
            {
                "document_number": nfse.numero,
                "verify_code": nfse.codigo_verificacao,
                "nfse_giss_national_key": nfse.chave_nacional or False,
                "authorization_date": authorization_date,
                "status_code": "4",
                "status_name": self.env._("Processado com sucesso"),
                "edoc_error_message": False,
            }
        )
        if self.authorization_event_id:
            self.authorization_event_id.set_done(
                status_code=4,
                response=self.status_name,
                protocol_date=authorization_date,
                protocol_number=self.authorization_protocol or nfse.codigo_verificacao,
                file_response_xml=nfse.xml,
            )
        self._change_state(SITUACAO_EDOC_AUTORIZADA)
        self.make_pdf()

    def _giss_reject(self, retorno):
        self.ensure_one()
        self.write(
            {
                "status_code": "3",
                "status_name": self.env._("Processado com erro"),
                "edoc_error_message": retorno.mensagem,
                # a rejected lot is sent again as a new lot
                "authorization_protocol": False,
            }
        )
        self._change_state(SITUACAO_EDOC_REJEITADA)

    def _giss_process_lot(self, retorno):
        """Apply the answer of ``ConsultarLoteRps`` (or of the query by RPS)."""
        self.ensure_one()
        if retorno.nfses and not retorno.mensagens:
            self._giss_authorize(retorno)
        elif retorno.em_processamento and not retorno.mensagens:
            self.write(
                {
                    "status_code": retorno.situacao,
                    "status_name": self.env._(
                        "Lote em processamento na prefeitura: consulte a situação "
                        "do documento em instantes"
                    ),
                    "edoc_error_message": False,
                }
            )
            self._change_state(SITUACAO_EDOC_ENVIADA)
        else:
            self._giss_reject(retorno)

    def _eletronic_document_send(self):
        result = super()._eletronic_document_send()
        for record in self.filtered(filter_processador_edoc_nfse).filtered(filter_giss):
            provider = record._giss_provider()
            if not record.authorization_protocol:
                # The RPS number is the idempotency key: after a dropped
                # connection the lot may have been received, and sending it
                # again is refused (E10, E71, E233). Ask for the RPS first.
                anterior = provider.consultar_nfse_rps(
                    record.rps_number, record.document_serie_id.code or ""
                )
                if anterior.nfses and not anterior.nfses[0].cancelada:
                    record._giss_authorize(anterior)
                    continue
                xml = XmlSerializer().render(record._serialize_nfse_giss())
                envio_lote = provider.recepcionar_lote_rps(xml)
                if not envio_lote.sucesso or not envio_lote.protocolo:
                    record._giss_reject(envio_lote)
                    continue
                record.authorization_protocol = envio_lote.protocolo
            record._giss_process_lot(
                provider.aguardar_lote(record.authorization_protocol)
            )
        return result

    def _document_status(self):
        status = super()._document_status()
        for record in self.filtered(filter_processador_edoc_nfse).filtered(filter_giss):
            provider = record._giss_provider()
            if record.authorization_protocol and not record.document_number:
                retorno = provider.consultar_lote_rps(record.authorization_protocol)
            else:
                retorno = provider.consultar_nfse_rps(
                    record.rps_number, record.document_serie_id.code or ""
                )
            if record.state_edoc != SITUACAO_EDOC_AUTORIZADA and (
                retorno.nfses or retorno.situacao
            ):
                record._giss_process_lot(retorno)
            status = retorno.mensagem or record.status_name
        return status

    def _giss_cancel(self):
        self.ensure_one()
        if not self.document_number:
            raise UserError(self.env._("The NFS-e has no number to cancel."))
        provider = self._giss_provider()
        retorno = provider.cancelar_nfse(
            self.document_number,
            self.nfse_giss_cancel_code or CANCELAMENTO_ERRO_EMISSAO,
        )
        if not retorno.sucesso:
            raise UserError(
                self.env._(
                    "The city hall refused the cancellation:\n%(message)s",
                    message=retorno.mensagem,
                )
            )
        self.cancel_event_id = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=self._giss_event_environment(),
            event_type="2",
            xml_file=retorno.xml_enviado,
            document_id=self,
        )
        self.cancel_event_id.set_done(
            status_code=4,
            response=self.env._("Cancelamento confirmado"),
            protocol_date=self._giss_datetime(retorno.data_cancelamento)
            or fields.Datetime.now(),
            protocol_number=self.verify_code,
            file_response_xml=retorno.xml_resposta,
        )
        return True

    def _before_document_cancel(self):
        result = super()._before_document_cancel()
        for record in self.filtered(filter_processador_edoc_nfse).filtered(filter_giss):
            if record.state_edoc == SITUACAO_EDOC_AUTORIZADA:
                record._giss_cancel()
        return result
