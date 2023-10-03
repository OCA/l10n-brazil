# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import re
from datetime import datetime

from erpbrasil.assinatura import certificado as cert
from erpbrasil.transmissao import TransmissaoSOAP
from nfelib.cte.bindings.v4_0.cte_v4_00 import Cte
from requests import Session

from odoo import _, api, fields
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    AUTORIZADO,
    CANCELADO,
    CANCELADO_DENTRO_PRAZO,
    CANCELADO_FORA_PRAZO,
    DENEGADO,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    LOTE_PROCESSADO,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
)
from odoo.addons.spec_driven_model.models import spec_models

from ..constants.modal import CTE_MODAL_VERSION_DEFAULT, FERROV_TPTRAF

_logger = logging.getLogger(__name__)
try:
    pass
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


def filter_processador_edoc_cte(record):
    if record.processador_edoc == "oca" and record.document_type_id.code in [
        "57",
        "67",
    ]:
        return True
    return False


class CTe(spec_models.StackedModel):

    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "cte.40.tcte_infcte", "cte.40.tcte_fat"]
    _stacked = "cte.40.tcte_infcte"
    _field_prefix = "cte40_"
    _schema_name = "cte"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_cte"
    _spec_module = "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    _binding_module = "nfelib.cte.bindings.v4_0.cte_tipos_basico_v4_00"
    _cte_search_keys = ["cte40_Id"]

    INFCTE_TREE = """
    > infCte
        > <ide>
        - <toma> res.partner
        > <emit> res.company
        > <dest> res.partner
        > <vPrest>
        > <imp>
        - <ICMS>
        - <ICMSUFFim>
        > <infCTeNorm>
        - <infCarga>
        - <infModal>"""

    ##########################
    # CT-e spec related fields
    ##########################

    ##########################
    # CT-e tag: infCte
    ##########################

    cte40_versao = fields.Char(related="document_version")

    cte40_Id = fields.Char(
        compute="_compute_cte40_Id",
        inverse="_inverse_cte40_Id",
    )

    ##########################
    # CT-e tag: Id
    # Methods
    ##########################

    @api.depends("document_type_id", "document_key")
    def _compute_cte40_Id(self):
        for record in self.filtered(filter_processador_edoc_cte):
            if (
                record.document_type_id
                and record.document_type_id.prefix
                and record.document_key
            ):
                record.cte40_Id = "{}{}".format(
                    record.document_type_id.prefix, record.document_key
                )
            else:
                record.cte40_Id = False

    def _inverse_cte40_Id(self):
        for record in self:
            if record.cte40_Id:
                record.document_key = re.findall(r"\d+", str(record.cte40_Id))[0]

    ##########################
    # CT-e tag: ide
    ##########################

    cte40_cUF = fields.Char(
        related="company_id.partner_id.state_id.ibge_code",
        string="cte40_cUF",
    )

    cte40_cCT = fields.Char(related="document_key")

    cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP",
    )

    cte40_CFOP = fields.Char(related="cfop_id.code")

    cte40_natOp = fields.Char(related="operation_name")

    cte40_mod = fields.Char(related="document_type_id.code", string="cte40_mod")

    cte40_serie = fields.Char(related="document_serie")

    cte40_nCT = fields.Char(related="document_number")

    cte40_dhEmi = fields.Datetime(related="document_date")

    cte40_cDV = fields.Char(compute="_compute_cDV", store=True)

    cte40_procEmi = fields.Selection(default="0")

    cte40_verProc = fields.Char(
        copy=False,
        default=lambda s: s.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_cte.version.name", default="Odoo Brasil OCA v14"),
    )

    cte40_cMunEnv = fields.Char(compute="_compute_cte40_data", store=True)

    cte40_xMunEnv = fields.Char(compute="_compute_cte40_data", store=True)

    cte40_UFEnv = fields.Char(
        compute="_compute_cte40_data", string="cte40_UFEnv", store=True
    )

    # cte40_indIEToma = fields.Char(related="partner_id.incr_est", store=True)

    cte40_cMunIni = fields.Char(compute="_compute_cte40_data", store=True)

    cte40_xMunIni = fields.Char(compute="_compute_cte40_data", store=True)

    cte40_UFIni = fields.Char(compute="_compute_cte40_data", store=True)

    cte40_cMunFim = fields.Char(
        compute="_compute_cte40_data",
        related="partner_id.city_id.ibge_code",
        store=True,
    )

    cte40_xMunFim = fields.Char(
        compute="_compute_cte40_data", related="partner_id.city_id.name", store=True
    )

    cte40_UFFim = fields.Char(
        compute="_compute_cte40_data", string="cte40_cUF", store=True
    )

    cte40_retira = fields.Selection(selection=[("0", "Sim"), ("1", "Não")], default="1")

    cte40_tpServ = fields.Selection(
        selection=[
            ("6", "Transporte de Pessoas"),
            ("7", "Transporte de Valores"),
            ("8", "Excesso de Bagagem"),
        ],
        default="6",
    )

    cte40_tpCTe = fields.Selection(
        selection=[
            ("0", "CTe Normal"),
            ("1", "CTe Complementar"),
            ("3", "CTe Substituição"),
        ],
        default="0",
    )

    cte40_tpAmb = fields.Selection(
        selection=[("1", "Produção"), ("2", "Homologação")],
        string="CTe Environment",
        copy=False,
        default="2",
    )

    cte40_tpEmis = fields.Selection(
        selection=[
            ("1", "Normal"),
            ("3", "Regime Especial NFF"),
            ("4", "EPEC pela SVC"),
        ],
        default="1",
    )

    cte40_tpImp = fields.Selection(
        selection=[("1", "Retrato"), ("2", "Paisagem")], default="1"
    )

    def _export_fields_cte_40_toma3(self, xsd_fields, class_obj, export_dict):
        if self.cte40_choice_toma == "cte40_toma4":
            xsd_fields.remove("cte40_toma")

    def _export_fields_cte_40_tcte_toma4(self, xsd_fields, class_obj, export_dict):
        if self.cte40_choice_toma == "cte40_toma3":
            xsd_fields.remove("cte40_toma")
            xsd_fields.remove("cte40_CNPJ")
            xsd_fields.remove("cte40_CPF")
            xsd_fields.remove("cte40_IE")
            xsd_fields.remove("cte40_xNome")
            xsd_fields.remove("cte40_xFant")
            xsd_fields.remove("cte40_enderToma")

    # toma
    cte40_choice_toma = fields.Selection(
        selection=[
            ("cte40_toma3", "toma3"),
            ("cte40_toma4", "toma4"),
        ],
        compute="_compute_toma",
        store=True,
    )

    cte40_toma = fields.Selection(related="service_provider")

    cte40_CNPJ = fields.Char(
        related="partner_id.cte40_CNPJ",
    )
    cte40_CPF = fields.Char(
        related="partner_id.cte40_CPF",
    )
    cte40_IE = fields.Char(
        related="partner_id.cte40_IE",
    )
    cte40_xNome = fields.Char(
        related="partner_id.legal_name",
    )
    cte40_xFant = fields.Char(
        related="partner_id.name",
    )

    cte40_enderToma = fields.Many2one(comodel_name="res.partner", related="partner_id")

    ##########################
    # CT-e tag: ide
    # Compute Methods
    ##########################

    @api.depends("service_provider")
    def _compute_toma(self):
        for doc in self:
            if doc.service_provider in ["0", "1", "2", "3"]:
                doc.cte40_choice_toma = "cte40_toma3"
            else:
                doc.cte40_choice_toma = "cte40_toma4"

    def _compute_cDV(self):
        for rec in self:
            if rec.document_key:
                rec.cte40_cDV = rec.document_key[:-1]

    @api.depends("partner_id", "company_id")
    def _compute_cte40_data(self):
        for doc in self:
            if doc.company_id.partner_id.country_id == doc.partner_id.country_id:
                doc.cte40_xMunIni = doc.company_id.partner_id.city_id.name
                doc.cte40_cMunIni = doc.company_id.partner_id.city_id.ibge_code
                doc.cte40_xMunEnv = doc.company_id.partner_id.city_id.name
                doc.cte40_cMunEnv = doc.company_id.partner_id.city_id.ibge_code
                doc.cte40_UFEnv = doc.company_id.partner_id.state_id.code
                doc.cte40_UFIni = doc.company_id.partner_id.state_id.ibge_code
                doc.cte40_cMunFim = doc.partner_id.city_id.ibge_code
                doc.cte40_xMunFim = doc.partner_id.city_id.name
                doc.cte40_UFFim = doc.partner_id.state_id.code
            else:
                doc.cte40_UFIni = "EX"
                doc.cte40_UFEnv = "EX"
                doc.cte40_xMunIni = "EXTERIOR"
                doc.cte40_cMunIni = "9999999"
                doc.cte40_xMunEnv = (
                    doc.company_id.partner_id.country_id.name
                    + "/"
                    + doc.company_id.partner_id.city_id.name
                )
                doc.cte40_cMunEnv = "9999999"
                doc.cte40_cMunFim = "9999999"
                doc.cte40_xMunFim = "EXTERIOR"
                doc.cte40_UFFim = "EX"

    ##########################
    # CT-e tag: emit
    ##########################

    cte40_emit = fields.Many2one(
        comodel_name="res.company",
        compute="_compute_emit_data",
        readonly=True,
        string="Emit",
    )

    cte40_CRT = fields.Selection(
        related="company_tax_framework",
        string="Código de Regime Tributário (NFe)",
    )

    ##########################
    # CT-e tag: emit
    # Compute Methods
    ##########################

    def _compute_emit_data(self):
        for doc in self:  # TODO if out
            doc.cte40_emit = doc.company_id

    ##########################
    # CT-e tag: rem
    ##########################

    cte40_rem = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_rem_data",
        readonly=True,
        string="Rem",
    )

    ##########################
    # CT-e tag: rem
    # Compute Methods
    ##########################

    def _compute_rem_data(self):
        for doc in self:  # TODO if out
            doc.cte40_rem = doc.partner_id

    ##########################
    # CT-e tag: exped
    ##########################

    cte40_exped = fields.Many2one(
        comodel_name="res.company",
        compute="_compute_exped_data",
        readonly=True,
        string="Exped",
    )

    ##########################
    # CT-e tag: exped
    # Compute Methods
    ##########################

    def _compute_exped_data(self):
        for doc in self:  # TODO if out
            doc.cte40_exped = doc.company_id

    ##########################
    # CT-e tag: dest
    ##########################

    cte40_dest = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_dest_data",
        readonly=True,
        string="Dest",
    )

    ##########################
    # CT-e tag: dest
    # Compute Methods
    ##########################

    def _compute_dest_data(self):
        for doc in self:  # TODO if out
            doc.cte40_dest = doc.partner_shipping_id

    ##########################
    # CT-e tag: imp TODO
    ##########################

    cte40_imp = fields.One2many(
        comodel_name="l10n_br_fiscal.document.line",
        inverse_name="document_id",
        related="fiscal_line_ids",
    )

    ##########################
    # CT-e tag: imp
    # Compute Methods
    ##########################

    def _compute_imp(self):
        for doc in self:
            doc.cte40_ICMS = doc.fiscal_line_ids

    #####################################
    # CT-e tag: infCTeNorm and infCteComp
    #####################################

    cte40_choice_infcteNorm_infcteComp = fields.Selection(
        selection=[
            ("cte40_infCTeComp", "infCTeComp"),
            ("cte40_infCTeNorm", "infCTeNorm"),
        ],
        default="cte40_infCTeNorm",
    )

    cte40_infCarga = fields.One2many(
        comodel_name="l10n_br_fiscal.document.related",
        string="Informações de quantidades da Carga do CTe",
        inverse_name="document_id",
    )

    cte40_infCTeNorm = fields.One2many(
        comodel_name="l10n_br_fiscal.document.related",
        inverse_name="document_id",
    )

    cte40_infCTeComp = fields.One2many(
        comodel_name="l10n_br_fiscal.document.related",
        inverse_name="document_id",
    )

    ##########################
    # CT-e tag: autXML
    # Compute Methods
    ##########################

    def _default_cte40_autxml(self):
        company = self.env.company
        authorized_partners = []
        if company.accountant_id and company.cte_authorize_accountant_download_xml:
            authorized_partners.append(company.accountant_id.id)
        if (
            company.technical_support_id
            and company.cte_authorize_technical_download_xml
        ):
            authorized_partners.append(company.technical_support_id.id)
        return authorized_partners

    ##########################
    # CT-e tag: autXML
    ##########################

    cte40_autXML = fields.One2many(default=_default_cte40_autxml)

    ##########################
    # CT-e tag: infmodal
    ##########################

    cte40_modal = fields.Selection(related="transport_modal")

    cte40_versaoModal = fields.Char(CTE_MODAL_VERSION_DEFAULT)

    # Campos do Modal Aereo
    modal_aereo_id = fields.Many2one(comodel_name="l10n_br_cte.modal.aereo")

    flight_delivery_forecast = fields.Date(
        string="Data prevista da entrega",
        help="Data prevista da entrega\nFormato AAAA-MM-DD",
    )

    # Campos do Modal Aquaviario
    modal_aquaviario_id = fields.Many2one(comodel_name="l10n_br_cte.modal.aquaviario")

    ship_installment_value = fields.Monetary(
        compute="_compute_installment_value", store=True
    )

    ship_vAFRMM = fields.Monetary(
        string="AFRMM",
        currency_field="brl_currency_id",
        help=("AFRMM (Adicional de Frete para Renovação da Marinha Mercante)"),
    )

    ship_name = fields.Char(string="Identificação do Navio")

    ship_travel_number = fields.Char(string="Número da Viagem")

    ship_direction = fields.Selection(
        selection=[
            ("N", "Norte, L-Leste, S-Sul, O-Oeste"),
            ("S", "Sul, O-Oeste"),
            ("L", "Leste, S-Sul, O-Oeste"),
            ("O", "Oeste"),
        ],
        string="Direção",
        help="Direção\nPreencher com: N-Norte, L-Leste, S-Sul, O-Oeste",
    )

    ship_irin = fields.Char(
        string="Irin do navio sempre deverá",
        help="Irin do navio sempre deverá ser informado",
    )

    ship_type = fields.Selection(
        selection=[
            ("0", "Interior"),
            ("1", "Cabotagem"),
        ],
        string="Tipo de Navegação",
        help=(
            "Tipo de Navegação\nPreencher com: \n\t\t\t\t\t\t0 - "
            "Interior;\n\t\t\t\t\t\t1 - Cabotagem"
        ),
    )

    # Campos do Modal Dutoviario
    modal_dutoviario_id = fields.Many2one(comodel_name="l10n_br_cte.modal.dutoviario")

    pipeline_initial_date = fields.Date(string="Data de Início da prestação do serviço")

    pipeline_final_date = fields.Date(string="Data de Fim da prestação do serviço")

    pipeline_fare_value = fields.Float(string="Valor da tarifa")

    # Campos do Modal Ferroviario TODO
    modal_ferroviario_id = fields.Many2one(comodel_name="l10n_br_cte.modal.ferroviario")

    railroad_traffic_type = fields.Selection(
        selection=FERROV_TPTRAF,
        default="0",
    )

    railroad_flow = fields.Char(
        string="Fluxo Ferroviário",
        help=(
            "Fluxo Ferroviário\nTrata-se de um número identificador do "
            "contrato firmado com o cliente"
        ),
    )

    cte40_vFrete = fields.Monetary(
        related="amount_freight_value",
        currency_field="brl_currency_id",
    )

    cte40_respFat = fields.Selection(
        selection=[
            ("1", "Ferrovia de origem"),
            ("2", "Ferrovia de destino"),
        ]
    )

    cte40_ferrEmi = fields.Selection(
        selection=[
            ("1", "Ferrovia de origem"),
            ("2", "Ferrovia de destino"),
        ],
        string="Ferrovia Emitente do CTe",
        help=(
            "Ferrovia Emitente do CTe\nPreencher com: "
            "\n\t\t\t\t\t\t\t\t\t1-Ferrovia de origem; "
            "\n\t\t\t\t\t\t\t\t\t2-Ferrovia de destino"
        ),
    )

    cte40_ferroEnv = fields.One2many(
        comodel_name="l10n_br_cte.modal.ferroviario.trafmut.ferroenv",
        inverse_name="document_id",
        string="Informações das Ferrovias Envolvidas",
    )

    # Campos do Modal rodoviario TODO
    modal_rodoviario_id = fields.Many2one(comodel_name="l10n_br_cte.modal.rodoviario")

    cte40_RNTRC = fields.Char(
        string="RNTRC",
        store=True,
        related="partner_id.rntrc_code",
        help="Registro Nacional de Transportadores Rodoviários de Carga",
    )

    occ = fields.One2many(
        comodel_name="l10n_br_cte.modal.rodoviario.occ",
        inverse_name="document_id",
        string="Ordens de Coleta associados",
    )

    ##########################
    # CT-e tag: infmodal
    # Compute Methods
    ##########################

    def _compute_installment_value(self):
        vPrest = 0
        for record in self.fiscal_line_ids:
            vPrest += record.cte40_vTPrest
        self.ship_installment_value = vPrest

    def _export_fields_cte_40_infmodal(self, xsd_fields, class_obj, export_dict):
        self = self.with_context(module="l10n_br_cte")

        if self.cte_modal == "1":
            export_dict["any_element"] = self._export_modal_rodoviario()
        elif self.cte_modal == "2":
            export_dict["any_element"] = self._export_modal_aereo()
        elif self.cte_modal == "3":
            export_dict["any_element"] = self._export_modal_aquaviario()
        elif self.cte_modal == "4":
            export_dict["any_element"] = self._export_modal_ferroviario()

    def _export_modal_aereo(self):
        if not self.modal_aereo_id:
            self.modal_aereo_id = self.modal_aereo_id.create({"document_id": self.id})

        return self.modal_aereo_id.export_ds()[0]

    def _export_modal_ferroviario(self):
        if not self.modal_ferroviario_id:
            self.modal_ferroviario_id = self.modal_ferroviario_id.create(
                {"document_id": self.id}
            )

        return self.modal_ferroviario_id.export_ds()[0]

    def _export_modal_aquaviario(self):
        if not self.modal_aquaviario_id:
            self.modal_aquaviario_id = self.modal_aquaviario_id.create(
                {"document_id": self.id}
            )

        return self.modal_aquaviario_id.export_ds()[0]

    def _export_modal_rodoviario(self):
        if not self.modal_rodoviario_id:
            self.modal_rodoviario_id = self.modal_rodoviario_id.create(
                {"document_id": self.id}
            )

        return self.modal_rodoviario_id.export_ds()[0]

    ################################
    # Business Model Methods
    ################################

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.with_context(lang="pt_BR").filtered(
            filter_processador_edoc_cte
        ):
            inf_cte = record.export_ds()[0]
            cte = Cte(infCte=inf_cte, infCTeSupl=None, signature=None)
            edocs.append(cte)
        return edocs

    def _processador(self):
        if not self.company_id.certificate_nfe_id:
            raise UserError(_("Certificado não encontrado"))

        certificado = cert.Certificado(
            arquivo=self.company_id.certificate_nfe_id.file,
            senha=self.company_id.certificate_nfe_id.password,
        )
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(certificado, session)
        return Cte(
            transmissao,
            self.company_id.state_id.ibge_code,
        )

    def _document_export(self, pretty_print=True):
        result = super()._document_export()
        for record in self.filtered(filter_processador_edoc_cte):
            edoc = record.serialize()[0]
            record._processador()
            xml_file = edoc.to_xml()
            event_id = self.event_ids.create_event_save_xml(
                company_id=self.company_id,
                environment=(
                    EVENT_ENV_PROD if self.cte40_tpAmb == "1" else EVENT_ENV_HML
                ),
                event_type="0",
                xml_file=xml_file,
                document_id=self,
            )
            record.authorization_event_id = event_id
            # xml_assinado = processador.assinar_edoc(edoc, edoc.infCte.Id)
            # self._valida_xml(xml_assinado)
        return result

    # def _valida_xml(self, xml_file):
    #     self.ensure_one()
    #     erros = Cte.schema_validation(xml_file)
    #     erros = "\n".join(erros)
    #     self.write({"xml_error_message": erros or False})

    def atualiza_status_cte(self, infProt, xml_file):
        self.ensure_one()
        if infProt.cStat in AUTORIZADO:
            state = SITUACAO_EDOC_AUTORIZADA
        elif infProt.cStat in DENEGADO:
            state = SITUACAO_EDOC_DENEGADA
        else:
            state = SITUACAO_EDOC_REJEITADA
        if self.authorization_event_id and infProt.nProt:
            if type(infProt.dhRecbto) == datetime:
                protocol_date = fields.Datetime.to_string(infProt.dhRecbto)
            else:
                protocol_date = fields.Datetime.to_string(
                    datetime.fromisoformat(infProt.dhRecbto)
                )

            self.authorization_event_id.set_done(
                status_code=infProt.cStat,
                response=infProt.xMotivo,
                protocol_date=protocol_date,
                protocol_number=infProt.nProt,
                file_response_xml=xml_file,
            )
        self.write(
            {
                "status_code": infProt.cStat,
                "status_name": infProt.xMotivo,
            }
        )
        self._change_state(state)

    def _eletronic_document_send(self):
        super(CTe, self)._eletronic_document_send()
        for record in self.filtered(filter_processador_edoc_cte):
            if self.xml_error_message:
                return
            record._processador()
            for _edoc in record.serialize():
                processo = None
                # for p in processador.processar_documento(edoc):
                #     processo = p
                if processo.webservice == "cteAutorizacaoLote":
                    record.authorization_event_id._save_event_file(
                        processo.envio_xml.decode("utf-8"), "xml"
                    )

            if processo.resposta.cStat in LOTE_PROCESSADO + ["100"]:
                record.atualiza_status_cte(
                    processo.protocolo.infProt, processo.processo_xml.decode("utf-8")
                )
            elif processo.resposta.cStat == "225":
                state = SITUACAO_EDOC_REJEITADA

                record._change_state(state)

                record.write(
                    {
                        "status_code": processo.resposta.cStat,
                        "status_name": processo.resposta.xMotivo,
                    }
                )
        return

    def _document_cancel(self, justificative):
        result = super(CTe, self)._document_cancel(justificative)
        online_event = self.filtered(filter_processador_edoc_cte)
        if online_event:
            online_event._cte_cancel()
        return result

    def _cte_cancel(self):
        self.ensure_one()
        processador = self._processador()

        if not self.authorization_protocol:
            raise UserError(_("Authorization Protocol Not Found!"))

        evento = processador.cancela_documento(
            chave=self.document_key,
            protocolo_autorizacao=self.authorization_protocol,
            justificativa=self.cancel_reason.replace("\n", "\\n"),
        )
        processo = processador.enviar_lote_evento(lista_eventos=[evento])

        self.cancel_event_id = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=(
                EVENT_ENV_PROD if self.cte_environment == "1" else EVENT_ENV_HML
            ),
            event_type="2",
            xml_file=processo.envio_xml.decode("utf-8"),
            document_id=self,
        )

        for retevento in processo.resposta.retEvento:
            if not retevento.infEvento.chCte == self.document_key:
                continue

            if retevento.infEvento.cStat not in CANCELADO:
                mensagem = "Erro no cancelamento"
                mensagem += "\nCódigo: " + retevento.infEvento.cStat
                mensagem += "\nMotivo: " + retevento.infEvento.xMotivo
                raise UserError(mensagem)

            if retevento.infEvento.cStat == CANCELADO_FORA_PRAZO:
                self.state_fiscal = SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO
            elif retevento.infEvento.cStat == CANCELADO_DENTRO_PRAZO:
                self.state_fiscal = SITUACAO_FISCAL_CANCELADO

            self.state_edoc = SITUACAO_EDOC_CANCELADA
            self.cancel_event_id.set_done(
                status_code=retevento.infEvento.cStat,
                response=retevento.infEvento.xMotivo,
                protocol_date=fields.Datetime.to_string(
                    datetime.fromisoformat(retevento.infEvento.dhRegEvento)
                ),
                protocol_number=retevento.infEvento.nProt,
                file_response_xml=processo.retorno.content.decode("utf-8"),
            )
