# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime

from erpbrasil.base import misc
from nfselib.paulistana.v02 import PedidoEnvioLoteRPS as lote_rps_v02
from nfselib.paulistana.v02.PedidoEnvioLoteRPS import (
    CabecalhoType,
    tpCPFCNPJ,
    tpEndereco,
    tpRPS,
)
from nfselib.paulistana.v03 import PedidoEnvioLoteRPS as lote_rps_v03
from unidecode import unidecode

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    MODELO_FISCAL_NFSE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_REJEITADA,
)

from ..constants.paulistana import CONSULTA_LOTE, ENVIO_LOTE_RPS

_logger = logging.getLogger(__name__)

# Legacy layout (taxable event until 2025-12-31) = nfselib v02 bindings,
# Versao=1. Tax reform layout (IBS/CBS) = nfselib v03 bindings, Versao=2.
PAULISTANA_BINDINGS = {
    "v02": {"module": lote_rps_v02, "versao": 1},
    "v03": {"module": lote_rps_v03, "versao": 2},
}

# Schema types with fractionDigits=4. The remaining decimals are monetary
# (tpValor, fractionDigits=2); rounding a rate to 2 places would corrupt the
# value (e.g. 0.029 -> 0.03).
DECIMAL_4_TYPES = ("tpAliquota", "tpPercentualCargaTributaria")


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

    nfse_document_key = fields.Char(
        string="NFS-e National Key",
        copy=False,
        index=True,
        help=(
            "National access key of the NFS-e (tax reform, "
            "ChaveNotaNacional). It has 50 digits, unlike document_key, which "
            "is the 44 digit key of NF-e/NFC-e/CT-e validated by _check_key."
        ),
    )

    def convert_type_nfselib(self, class_object, object_filed, value):
        if value is None:
            return value

        value_type = ""
        restriction_type = ""
        for field in class_object().member_data_items_:
            if field.name == object_filed:
                value_type = field.child_attrs.get("type", "").replace("xs:", "")
                # data_type is the schema restriction chain, e.g.
                # ['tpAliquota', 'xs:decimal']; the first item is the named
                # type, which is what defines fractionDigits.
                data_type = getattr(field, "data_type", None)
                if isinstance(data_type, list | tuple) and data_type:
                    restriction_type = data_type[0]
                break

        if value_type in ("int", "long", "byte", "nonNegativeInteger"):
            return int(value)
        elif value_type == "decimal":
            decimals = 4 if restriction_type in DECIMAL_4_TYPES else 2
            return round(float(value), decimals)
        elif value_type == "string":
            return str(value)
        else:
            return value

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_oca_nfse).filtered(filter_paulistana):
            nfse_version = record.company_id.nfse_paulistana_schema or "v02"
            edocs.append(record.serialize_nfse_paulistana(nfse_version=nfse_version))
        return edocs

    def _processador_erpbrasil_nfse(self, **kwargs):
        # Forward the schema version configured on the company to the
        # erpbrasil.edoc provider, so that the query and cancellation envelopes
        # use the same layout as the RPS (Versao 1 legacy / Versao 2 tax
        # reform). l10n_br_nfse drops the parameter, with a warning in the log,
        # while the installed library version does not accept it - see ROADMAP.
        if self.company_id.provedor_nfse == "paulistana":
            kwargs.setdefault(
                "versao_schema", self.company_id.nfse_paulistana_schema or "v02"
            )
        return super()._processador_erpbrasil_nfse(**kwargs)

    def serialize_nfse_paulistana(self, nfse_version="v02"):
        binding = PAULISTANA_BINDINGS[nfse_version]
        dados_lote_rps = self._prepare_lote_rps()
        dados_servico = self._prepare_dados_servico()
        lote_rps = binding["module"].PedidoEnvioLoteRPS(
            Cabecalho=self._serialize_cabecalho(dados_lote_rps, binding),
            RPS=[self._serialize_lote_rps(dados_lote_rps, dados_servico, binding)],
        )
        return lote_rps

    def _serialize_cabecalho(self, dados_lote_rps, binding=None):
        binding = binding or PAULISTANA_BINDINGS["v02"]
        CabecalhoType = binding["module"].CabecalhoType
        tpCPFCNPJ = binding["module"].tpCPFCNPJ
        return CabecalhoType(
            Versao=self.convert_type_nfselib(
                CabecalhoType, "Versao", binding["versao"]
            ),
            CPFCNPJRemetente=tpCPFCNPJ(
                CNPJ=self.convert_type_nfselib(
                    CabecalhoType, "tpCPFCNPJ", dados_lote_rps["cnpj"]
                )
            ),
            transacao=False,  # TODO: Verficar origem do dado
            dtInicio=self.convert_type_nfselib(
                CabecalhoType,
                "dtInicio",
                dados_lote_rps["date_in_out"].split("T", 1)[0],
            ),
            dtFim=self.convert_type_nfselib(
                CabecalhoType, "dtFim", dados_lote_rps["date_in_out"].split("T", 1)[0]
            ),
            QtdRPS=self.convert_type_nfselib(CabecalhoType, "QtdRPS", "1"),
            ValorTotalServicos=self.convert_type_nfselib(
                CabecalhoType, "ValorTotalServicos", dados_lote_rps["total_recebido"]
            ),
            ValorTotalDeducoes=self.convert_type_nfselib(
                CabecalhoType, "ValorTotalDeducoes", dados_lote_rps["carga_tributaria"]
            ),
        )

    def _serialize_lote_rps(self, dados_lote_rps, dados_servico, binding=None):
        binding = binding or PAULISTANA_BINDINGS["v02"]
        tpRPS = binding["module"].tpRPS
        tpChaveRPS = binding["module"].tpChaveRPS
        tpCPFCNPJ = binding["module"].tpCPFCNPJ
        tpEndereco = binding["module"].tpEndereco
        dados_tomador = self._prepare_dados_tomador()
        assinatura = self.assinatura_rps(
            dados_lote_rps, dados_servico, dados_tomador, binding
        )
        if binding["versao"] >= 2:
            # Both schemas declare Assinatura as xs:base64Binary, but the v02
            # bindings write the raw value (they expect str, the base64 is done
            # by erpbrasil.edoc) while the v03 ones apply b64encode on export,
            # which requires bytes.
            assinatura = assinatura.encode("ascii")
        rps = tpRPS(
            Assinatura=assinatura,
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
            ValorServicos=self.convert_type_nfselib(
                tpRPS, "ValorServicos", dados_servico["valor_servicos"]
            ),
            ValorDeducoes=self.convert_type_nfselib(
                tpRPS, "ValorDeducoes", dados_servico["valor_deducoes"]
            ),
            ValorPIS=self.convert_type_nfselib(
                tpRPS, "ValorPIS", dados_servico["valor_pis_retido"]
            ),
            ValorCOFINS=self.convert_type_nfselib(
                tpRPS, "ValorCOFINS", dados_servico["valor_cofins_retido"]
            ),
            ValorINSS=self.convert_type_nfselib(
                tpRPS, "ValorINSS", dados_servico["valor_inss_retido"]
            ),
            ValorIR=self.convert_type_nfselib(
                tpRPS, "ValorIR", dados_servico["valor_ir_retido"]
            ),
            ValorCSLL=self.convert_type_nfselib(
                tpRPS, "ValorCSLL", dados_servico["valor_csll_retido"]
            ),
            CodigoServico=self.convert_type_nfselib(
                tpRPS, "CodigoServico", dados_servico["codigo_tributacao_municipio"]
            ),
            AliquotaServicos=self.convert_type_nfselib(
                tpRPS, "AliquotaServicos", dados_servico["aliquota"]
            ),
            ISSRetido="true" if dados_servico["iss_retido"] == "1" else "false",
            # FIXME: Hardcoded
            CPFCNPJTomador=self.convert_type_nfselib(
                tpRPS,
                "CPFCNPJTomador",
                tpCPFCNPJ(CNPJ=dados_tomador["cnpj"], CPF=dados_tomador["cpf"]),
            ),
            InscricaoMunicipalTomador=self.convert_type_nfselib(
                tpRPS,
                "InscricaoMunicipalTomador",
                dados_tomador["inscricao_municipal"],
            )
            if dados_tomador["codigo_municipio"]
            == int(self.company_id.partner_id.city_id.ibge_code)
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
                unidecode(
                    dados_servico["discriminacao"]
                    + (
                        "|{}|".format(self.fiscal_additional_data.replace("\n", "|"))
                        if self.fiscal_additional_data
                        else ""
                    )
                ),
            ),
            ValorCargaTributaria=self.convert_type_nfselib(
                tpRPS,
                "ValorCargaTributaria",
                dados_lote_rps["carga_tributaria_estimada"],
            ),
            PercentualCargaTributaria=self.convert_type_nfselib(
                tpRPS,
                "PercentualCargaTributaria",
                self._percentual_carga_tributaria(dados_lote_rps, dados_servico),
            ),
            FonteCargaTributaria=self.convert_type_nfselib(
                tpRPS, "FonteCargaTributaria", self._fonte_carga_tributaria()
            ),
            MunicipioPrestacao=self.convert_type_nfselib(
                CabecalhoType,
                "Versao",
                self._map_provision_municipality(
                    dados_lote_rps["natureza_operacao"],
                    dados_servico["codigo_municipio"],
                ),
            ),
        )
        if binding["versao"] >= 2:
            self._fill_rps_v03_required(rps, binding, dados_servico)
        return rps

    def _fill_rps_v03_required(self, rps, binding, dados_servico):
        """Fill the required fields that only exist in the tax reform layout.

        None of these elements exists in the v02 bindings - passing them to the
        legacy tpRPS would raise TypeError -, so they are filled after the RPS
        is built, and only when the schema is the tax reform one.
        """
        valor_servicos = round(float(dados_servico.get("valor_servicos") or 0), 2)
        # Charged base: the schema defines ValorInicialCobrado XOR
        # ValorFinalCobrado (xs:choice). São Paulo discontinued
        # ValorInicialCobrado (error 640); the current rule requires
        # ValorFinalCobrado.
        rps.ValorFinalCobrado = valor_servicos
        rps.ValorIPI = 0.0  # a service does not report IPI
        # TODO(MOC): map suspended enforceability and advance instalment
        # payment according to the fiscal scenario (0 = no).
        rps.ExigibilidadeSuspensa = 0
        rps.PagamentoParceladoAntecipado = 0
        # NBS must have 9 digits ([0-9]{9}): use the unmasked code.
        codigo_nbs = dados_servico.get("codigo_nbs_unmasked") or dados_servico.get(
            "codigo_nbs"
        )
        rps.NBS = re.sub(r"\D", "", codigo_nbs) if codigo_nbs else None
        # gpPrestacao is xs:choice (cLocPrestacao XOR cPaisPrestacao). Service
        # rendered in Brazil -> only the city (IBGE code).
        municipio_prestacao = dados_servico.get(
            "municipio_prestacao_servico"
        ) or dados_servico.get("codigo_municipio")
        rps.cLocPrestacao = int(municipio_prestacao) if municipio_prestacao else None
        rps.IBSCBS = self._serialize_ibscbs(binding, dados_servico)

    def _serialize_ibscbs(self, binding, dados_servico):
        """Build the IBSCBS group, required in the tax reform layout RPS.

        The submission carries the tax classification (cClassTrib) and the
        indicators; the IBS/CBS monetary values are computed and returned by
        the webservice in the response.
        """
        module = binding["module"]
        tpIBSCBS = module.tpIBSCBS
        tpValores = module.tpValores
        tpTrib = module.tpTrib
        tpGIBSCBS = module.tpGIBSCBS

        # The codes come from the fiscal configuration that already exists,
        # without asking the user for anything new: cClassTrib comes from the
        # line tax_classification_id (computed in _compute_fiscal_tax_ids
        # through map_fiscal_taxes), falling back to the company default;
        # cIndOp comes from the product operation_indicator_id.
        cclasstrib = dados_servico.get("ibs_cbs_classificacao_tributaria") or (
            self.company_id.tax_classification_id.code or None
        )
        cindop = dados_servico.get("codigo_indicador_operacao") or None
        if not cclasstrib or not cindop:
            # Does not block the issuing, but logs it: without these codes the
            # tax reform layout rejects the batch (error 1001).
            _logger.warning(
                "NFS-e Paulistana %s: incomplete IBSCBS (cClassTrib=%s, "
                "cIndOp=%s). Set up the Tax Classification (IBS/CBS) and the "
                "Operation Indicator to avoid the batch being rejected.",
                self.document_number or self.id,
                cclasstrib,
                cindop,
            )
        try:
            ind_final = int(self.ind_final) if self.ind_final else 0
        except (TypeError, ValueError):
            ind_final = 0

        return tpIBSCBS(
            finNFSe=0,  # 0 = regular NFS-e (only value the schema accepts)
            indFinal=ind_final,
            cIndOp=cindop,
            # 0 = the recipient is the customer itself (default case, with no
            # distinct recipient). 1 would require the <dest> group.
            indDest=0,
            valores=tpValores(
                trib=tpTrib(
                    gIBSCBS=tpGIBSCBS(cClassTrib=cclasstrib),
                ),
            ),
        )

    def _percentual_carga_tributaria(self, dados_lote_rps, dados_servico):
        """Percentage (fraction) of the IBPT estimated tax burden.

        Derived from the estimated value / service value ratio so that it is
        always consistent with the ValorCargaTributaria that is sent (e.g.
        183.12 / 8758.72 -> 0.0209). The tpPercentualCargaTributaria type
        accepts 4 decimal places.
        """
        valor = float(dados_servico.get("valor_servicos") or 0)
        if not valor:
            return 0.0
        carga = float(dados_lote_rps.get("carga_tributaria_estimada") or 0)
        return carga / valor

    def _fonte_carga_tributaria(self):
        """Source/version of the estimated tax burden (e.g. 'IBPT26.1.L').

        Derived from the `version` field of the latest IBPT record
        (l10n_br_fiscal.tax.estimate) for the NBS + company - the same origin
        as the estimated value -, which only carries the version ('26.1.L'); we
        prefix it with 'IBPT' to build the source São Paulo expects. Falls back
        to 'IBPT' when there is no version. Limited to 10 characters
        (tpFonteCargaTributaria).
        """
        fonte = "IBPT"
        nbs = self.fiscal_line_ids[:1].nbs_id
        if nbs:
            estimate = self.env["l10n_br_fiscal.tax.estimate"].search(
                [
                    ("nbs_id", "=", nbs.id),
                    ("company_id", "=", self.company_id.id),
                ],
                order="create_date DESC",
                limit=1,
            )
            if estimate.version:
                fonte = "IBPT" + estimate.version
        return fonte[:10]

    def _serialize_rps(self, dados):
        return tpRPS(
            InscricaoMunicipalTomador=self.convert_type_nfselib(
                tpRPS, "InscricaoMunicipalTomador", dados["inscricao_municipal"]
            ),
            CPFCNPJTomador=tpCPFCNPJ(
                Cnpj=self.convert_type_nfselib(tpCPFCNPJ, "Cnpj", dados["cnpj"]),
                Cpf=self.convert_type_nfselib(tpCPFCNPJ, "Cpf", dados["cpf"]),
            ),
            RazaoSocialTomador=self.convert_type_nfselib(
                tpRPS, "RazaoSocialTomador", dados["razao_social"]
            ),
            EnderecoTomador=tpEndereco(
                Logradouro=self.convert_type_nfselib(
                    tpEndereco, "Logradouro", dados["endereco"]
                ),
                NumeroEndereco=self.convert_type_nfselib(
                    tpEndereco, "NumeroEndereco", dados["numero"]
                ),
                ComplementoEndereco=self.convert_type_nfselib(
                    tpEndereco, "ComplementoEndereco", dados["complemento"]
                ),
                Bairro=self.convert_type_nfselib(tpEndereco, "Bairro", dados["bairro"]),
                Cidade=self.convert_type_nfselib(
                    tpEndereco, "Cidade", dados["codigo_municipio"]
                ),
                UF=self.convert_type_nfselib(tpEndereco, "UF", dados["uf"]),
                CEP=self.convert_type_nfselib(tpEndereco, "CEP", dados["cep"]),
            )
            or None,
        )

    def assinatura_rps(
        self, dados_lote_rps, dados_servico, dados_tomador, binding=None
    ):
        assinatura = ""

        # Provider municipal registration: the legacy layout uses 8 positions,
        # the tax reform one uses 12. São Paulo rebuilds the same string to
        # verify the RSA signature, so a wrong width causes error 1206.
        versao = binding["versao"] if binding else PAULISTANA_BINDINGS["v02"]["versao"]
        inscr_width = 12 if versao >= 2 else 8
        assinatura += dados_lote_rps["inscricao_municipal"].zfill(inscr_width)
        assinatura += dados_lote_rps["serie"].ljust(5, " ")
        assinatura += dados_lote_rps["numero"].zfill(12)
        assinatura += datetime.strptime(
            dados_lote_rps["data_emissao"], "%Y-%m-%dT%H:%M:%S"
        ).strftime("%Y%m%d")
        assinatura += self._map_taxation_rps(dados_lote_rps["natureza_operacao"])
        assinatura += "N"  # Corrigir - Verificar status do RPS
        assinatura += "S" if dados_servico["iss_retido"] == "1" else "N"
        assinatura += f"{dados_servico['valor_servicos']:.2f}".replace(".", "").zfill(
            15
        )
        assinatura += f"{dados_lote_rps['carga_tributaria']:.2f}".replace(
            ".", ""
        ).zfill(15)
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
                            # An Element with no children is falsy: with
                            # "if retorno" the whole handling (including the
                            # error one, which builds edoc_error_message) was
                            # silently skipped when the root came with no
                            # child elements.
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
                retorno_xml = ET.fromstring(processo.retorno)
                # The city hall returns the date in ISO 8601 with "T"
                # (e.g. 2026-07-07T12:07:03); the Odoo Datetime field expects
                # "YYYY-MM-DD HH:MM:SS". fromisoformat accepts both separators
                # and returns a datetime that Odoo stores directly.
                data_emissao = datetime.fromisoformat(consulta["data_emissao"])
                vals = {
                    "verify_code": consulta["codigo_verificacao"],
                    "document_number": consulta["numero"],
                    "authorization_date": data_emissao,
                }
                # The ChaveNotaNacional (50 digits) comes in the tax reform
                # layout response. It does not fit in document_key, which is
                # validated as an NF-e key (44 digits): we store it in
                # nfse_document_key. In the legacy layout the element does not
                # exist, findtext returns None and the field is left untouched.
                chave = retorno_xml.findtext(".//ChaveNotaNacional")
                if chave:
                    vals["nfse_document_key"] = chave
                record.write(vals)
                # StatusNFe: "N" = normal/authorized, "C" = cancelled. When the
                # city hall has already cancelled it, Odoo may have been left
                # authorized (e.g. a previous cancellation was rolled back).
                # Reconcile it.
                if retorno_xml.findtext(".//StatusNFe") == "C":
                    status = record._paulistana_sync_cancelada(retorno_xml)
                else:
                    record.authorization_event_id.set_done(
                        status_code=4,
                        response=_("Procesado com Sucesso"),
                        protocol_date=data_emissao,
                        protocol_number=consulta["codigo_verificacao"],
                        file_response_xml=processo.retorno,
                    )
                    # (AUTORIZADA, AUTORIZADA) does not exist in
                    # WORKFLOW_EDOC: without the guard, querying an already
                    # authorized invoice raised a UserError about the
                    # transition not being allowed.
                    if record.state_edoc != SITUACAO_EDOC_AUTORIZADA:
                        record._change_state(SITUACAO_EDOC_AUTORIZADA)
                    status = _("Procesado com Sucesso")
            else:
                # On error analisa_retorno_consulta returns the message (a
                # string); on success it returns a dict, which cannot be passed
                # to _().
                status = _(consulta)
        return status

    def _paulistana_sync_cancelada(self, retorno_xml):
        """Reflect in Odoo a cancellation already done at the city hall.

        Called by _document_status when the query returns StatusNFe="C". The
        transition to CANCELADA is done WITHOUT calling the cancellation
        webservice again (the invoice is already cancelled there), through the
        context flag read in _exec_before_SITUACAO_EDOC_CANCELADA.
        _document_cancel also syncs the account move (cancel_move_ids).
        """
        self.ensure_one()
        if self.state_edoc == SITUACAO_EDOC_CANCELADA:
            return _("Document already cancelled")
        data_cancelamento = retorno_xml.findtext(".//DataCancelamento")
        justificativa = _("Cancelled at the city hall (detected through a query).")
        if data_cancelamento:
            justificativa = "{} {}".format(
                justificativa,
                _("Cancellation date: %s") % data_cancelamento,
            )
        # _document_cancel is the canonical path: it stores the cancel_reason,
        # performs the state transition and, with l10n_br_account installed,
        # syncs the account move through cancel_move_ids.
        self.with_context(paulistana_skip_cancel_webservice=True)._document_cancel(
            justificativa
        )
        return _("Document cancelled at the city hall")

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

    def _exec_before_SITUACAO_EDOC_CANCELADA(self, old_state, new_state):
        result = super()._exec_before_SITUACAO_EDOC_CANCELADA(old_state, new_state)
        # The return value of this hook decides, in the l10n_br_fiscal_edi
        # _change_state, whether the state transition happens. Returning the
        # super() result when the document is not a Paulistana one keeps merely
        # installing this module from making the cancellation of
        # NF-e/CT-e/MDF-e fail silently.
        if not self.filtered(filter_oca_nfse).filtered(filter_paulistana):
            return result
        if self.env.context.get("paulistana_skip_cancel_webservice"):
            # The NFS-e was already cancelled at the city hall (reconciled
            # through the query in _paulistana_sync_cancelada): just carry out
            # the transition in Odoo, without sending the cancellation request
            # again.
            return True
        return self.cancel_document_paulistana()
