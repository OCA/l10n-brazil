# Copyright 2023 KMEE INFORMATICA LTDA
# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import gzip
import logging
import re
import string
import sys
from datetime import datetime
from enum import Enum

from erpbrasil.base.fiscal import cnpj_cpf
from erpbrasil.base.fiscal.edoc import ChaveEdoc

# TODO: precisa tratar
from lxml import etree
from nfelib.cte.bindings.v4_0.cte_v4_00 import Cte
from nfelib.cte.bindings.v4_0.proc_cte_v4_00 import CteProc

# TODO: precisa tratar nfelib
# from nfelib.nfe.ws.edoc_legacy import CTeAdapter as edoc_cte
from xsdata.formats.dataclass.parsers import XmlParser

from odoo import _, api, fields
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_cte_spec.models.v4_0.cte_modal_ferroviario_v4_00 import (
    FERROV_TPTRAF,
    TRAFMUT_FERREMI,
    TRAFMUT_RESPFAT,
)
from odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00 import (
    COMDATA_TPPER,
    SEMHORA_TPHOR,
)
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    AUTORIZADO,
    CANCELADO,
    CANCELADO_DENTRO_PRAZO,
    CANCELADO_FORA_PRAZO,
    DENEGADO,
    DOCUMENT_ISSUER_COMPANY,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    EVENTO_RECEBIDO,
    LOTE_PROCESSADO,
    MODELO_FISCAL_CTE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
)
from odoo.addons.l10n_br_fiscal.constants.icms import ICMS_CST, ICMS_SN_CST
from odoo.addons.spec_driven_model.models import spec_models

from ..constants.cte import (
    CTE_CST,
    CTE_ENVIRONMENTS,
    CTE_ICMS_SELECTION,
    CTE_INDIETOMA,
    CTE_INDIETOMA_DEFAULT,
    CTE_TPEMIS,
    CTE_TPEMIS_DEFAULT,
    CTE_TPIMP,
    CTE_TPIMP_DEFAULT,
    CTE_TPSERV,
    CTE_TPSERV_DEFAULT,
    CTE_TRANSMISSIONS,
    CTE_TYPE,
    CTE_TYPE_DEFAULT,
)
from ..constants.modal import CTE_MODAL_VERSION_DEFAULT

CTE_XML_NAMESPACE = {"cte": "http://www.portalfiscal.inf.br/cte"}


_logger = logging.getLogger(__name__)


def filter_processador_edoc_cte(record):
    if record.processador_edoc == "oca" and record.document_type_id.code in [
        "57",
        "67",
    ]:
        return True
    return False


class CTe(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document"
    _inherit = [
        "l10n_br_fiscal.document",
        "cte.40.tcte_infcte",
    ]
    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    )
    _cte40_stacking_mixin = "cte.40.tcte_infcte"
    _cte40_stacking_skip_paths = (
        "cte40_semData",
        "cte40_noPeriodo",
        "cte40_comHora",
        "cte40_noInter",
        #     "cte40_NFref_ide_id",
    )

    # all m2o at this level will be stacked even if not required:
    _cte40_stacking_force_paths = (
        "infcte.compl",
        # "infcte.compl.entrega",
    )
    _cte_search_keys = ["cte40_Id"]

    INFCTE_TREE = """
    > infCte
        > <ide>
            > <toma> res.partner
        > <compl>
            > <Entrega>
            - <xObs>
            ≡ <ObsCont>
            ≡ <ObsFisco>

        > <emit> res.company
        > <rem> res.company
        > <exped> res.partner
        > <receb> res.partner
        > <vPrest>
            ≡ <comp>
        > <imp>
            > <ICMS>
            > <ICMSUFFim>
        > <infCTeNorm>
            > <infCarga>
                ≡ <infQ>
            > <infDoc>
                ≡ <infNF>
                ≡ <infNFe>
                ≡ <infOutros>
        -   > <infModal>
        > <autXML>
        > <infRespTec>
    > <infCTeSupl>"""

    cte40_versao = fields.Char(related="document_version")

    cte_version = fields.Selection(
        string="CT-e Version",
        related="company_id.cte_version",
        readonly=False,
    )

    cte_environment = fields.Selection(
        selection=CTE_ENVIRONMENTS,
        string="CTe Environment",
        copy=False,
        default=lambda self: self.env.company.cte_environment,
    )

    cte_transmission = fields.Selection(
        selection=CTE_TRANSMISSIONS,
        string="CTE Transmission",
        copy=False,
        default=lambda self: self.env.company.cte_transmission,
    )

    ##########################
    # CT-e spec related fields
    ##########################

    ##########################
    # CT-e tag: infCte
    ##########################

    cte40_Id = fields.Char(
        compute="_compute_cte40_id",
        inverse="_inverse_cte40_id",
    )

    ##########################
    # CT-e tag: Id
    # Compute Methods
    ##########################

    @api.depends("document_type_id", "document_key")
    def _compute_cte40_id(self):
        """Set schema data which are not just related fields"""

        for record in self.filtered(filter_processador_edoc_cte):
            record.cte40_Id = False

            if (
                record.document_type_id
                and record.document_type_id.prefix
                and record.document_key
            ):
                record.cte40_Id = "{}{}".format(
                    record.document_type_id.prefix, record.document_key
                )

    ##########################
    # CT-e tag: id
    # Inverse Methods
    ##########################

    def _inverse_cte40_id(self):
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

    cte40_cCT = fields.Char(compute="_compute_cte40_cct")

    cte40_CFOP = fields.Char(compute="_compute_cte40_CFOP", store=True)

    cte40_natOp = fields.Char(related="operation_name")

    cte40_mod = fields.Char(related="document_type_id.code", string="cte40_mod")

    cte40_serie = fields.Char(related="document_serie")

    cte40_nCT = fields.Char(related="document_number")

    cte40_dhEmi = fields.Datetime(related="document_date")

    # TODO: Tratar/Avaliar
    # cte40_cDV = fields.Char(compute="_compute_cte40_cDV", store=True)
    # cte40_cDV = fields.Char(related="key_check_digit")

    cte40_procEmi = fields.Selection(default="0")

    cte40_verProc = fields.Char(
        copy=False,
        default=lambda s: s.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_cte.version.name", default="Odoo Brasil OCA"),
    )

    cte40_cMunEnv = fields.Char(
        compute="_compute_cte40_data",
        store=True,
        compute_sudo=True,
    )

    cte40_xMunEnv = fields.Char(
        compute="_compute_cte40_data",
        store=True,
        compute_sudo=True,
    )

    cte40_UFEnv = fields.Char(
        compute="_compute_cte40_data",
        store=True,
        compute_sudo=True,
    )

    cte40_indIEToma = fields.Selection(
        selection=CTE_INDIETOMA,
        default=CTE_INDIETOMA_DEFAULT,
    )

    cte40_cMunIni = fields.Char(
        compute="_compute_cte40_data",
        compute_sudo=True,
    )

    cte40_xMunIni = fields.Char(
        compute="_compute_cte40_data",
        compute_sudo=True,
    )

    cte40_UFIni = fields.Char()

    cte40_cMunFim = fields.Char(
        compute="_compute_cte40_data",
        compute_sudo=True,
    )

    cte40_xMunFim = fields.Char(
        compute="_compute_cte40_data",
        compute_sudo=True,
    )

    cte40_UFFim = fields.Char()

    cte40_retira = fields.Selection(selection=[("0", "Sim"), ("1", "Não")], default="1")

    cte40_tpServ = fields.Selection(
        selection=CTE_TPSERV,
        default=CTE_TPSERV_DEFAULT,
    )

    cte40_tpCTe = fields.Selection(
        selection=CTE_TYPE,
        default=CTE_TYPE_DEFAULT,
    )

    cte40_tpAmb = fields.Selection(related="cte_environment")

    cte40_tpEmis = fields.Selection(
        selection=CTE_TPEMIS,
        default=CTE_TPEMIS_DEFAULT,
    )

    cte40_tpImp = fields.Selection(selection=CTE_TPIMP, default=CTE_TPIMP_DEFAULT)

    # toma
    cte40_toma = fields.Selection(related="service_provider")

    cte40_choice_toma = fields.Selection(
        selection=[
            ("cte40_toma3", "toma3"),
            ("cte40_toma4", "toma4"),
        ],
        compute="_compute_cte40_choice_toma",
    )

    cte40_enderToma = fields.Many2one(comodel_name="res.partner", related="partner_id")

    cte40_enderReme = fields.Many2one(comodel_name="res.partner")

    ##########################
    # CT-e tag: ide
    # Compute Methods
    ##########################

    @api.depends("company_id", "partner_id", "service_provider")
    def _compute_cte40_choice_toma(self):
        for rec in self.filtered(filter_processador_edoc_cte):
            if rec.service_provider in ["0", "1", "2", "3"]:
                rec.cte40_choice_toma = "cte40_toma3"
            else:
                rec.cte40_choice_toma = "cte40_toma4"

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

    @api.depends("fiscal_line_ids", "fiscal_line_ids.cfop_id")
    def _compute_cte40_CFOP(self):
        for rec in self.filtered(filter_processador_edoc_cte):
            if rec.fiscal_line_ids:
                rec.cte40_CFOP = rec.fiscal_line_ids[0].cfop_id.code

    # TODO: Tratar
    # @api.depends("document_key")
    # def _compute_cte40_cDV(self):
    #     for rec in self.filtered(filter_processador_edoc_cte):
    #         if rec.document_key:
    #             rec.cte40_cDV = rec.document_key[-1]

    def _compute_cte40_cct(self):
        for rec in self.filtered(filter_processador_edoc_cte):
            if rec.document_key:
                rec.cte40_cCT = rec.document_key[35:43]

    @api.depends(
        "partner_id",
        "company_id",
        "partner_sendering_id",
        "partner_shippering_id",
        "partner_shipping_id",
        "partner_receivering_id",
    )
    def _compute_cte40_data(self):
        for doc in self.filtered(filter_processador_edoc_cte):
            if doc.company_id.partner_id.country_id == doc.partner_id.country_id:
                if doc.issuer == DOCUMENT_ISSUER_COMPANY:
                    doc.cte40_xMunEnv = (
                        doc.company_id.partner_id.city_id.name
                    )  # TODO: provavelmente vai depender de quem é o emissor
                else:
                    doc.cte40_xMunEnv = (
                        doc.partner_id.city_id.name
                    )  # TODO: provavelmente vai depender de quem é o emissor

                doc.cte40_cMunEnv = doc.company_id.partner_id.city_id.ibge_code
                doc.cte40_UFEnv = doc.company_id.partner_id.state_id.code
                doc.cte40_xMunIni = (
                    doc.cte40_exped.city_id.name or doc.cte40_rem.city_id.name
                )
                doc.cte40_cMunIni = (
                    doc.cte40_exped.city_id.ibge_code or doc.cte40_rem.city_id.ibge_code
                )
                doc.cte40_UFIni = (
                    doc.cte40_exped.state_id.code or doc.cte40_rem.state_id.code
                )
                doc.cte40_xMunFim = (
                    doc.cte40_receb.city_id.name or doc.cte40_dest.city_id.name
                )
                doc.cte40_cMunFim = (
                    doc.cte40_receb.city_id.ibge_code
                    or doc.cte40_dest.city_id.ibge_code
                )
                doc.cte40_UFFim = (
                    doc.cte40_receb.state_id.code or doc.cte40_dest.state_id.code
                )
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

    # TODO: nao esta rodando direto.. corrigir
    def _compute_cte40_infQ(self):
        for record in self.filtered(filter_processador_edoc_cte):
            cargo_info_vals = [
                {"cte40_cUnid": "01", "cte40_tpMed": "Peso Bruto", "cte40_qCarga": 0},
                {
                    "cte40_cUnid": "01",
                    "cte40_tpMed": "Peso Base Calculado",
                    "cte40_qCarga": 0,
                },
                {"cte40_cUnid": "01", "cte40_tpMed": "Peso Aferido", "cte40_qCarga": 0},
                {"cte40_cUnid": "00", "cte40_tpMed": "Cubagem", "cte40_qCarga": 0},
                {"cte40_cUnid": "03", "cte40_tpMed": "Unidade", "cte40_qCarga": 0},
            ]

            record.cte40_infQ = self.env["l10n_br_cte.cargo.quantity.infos"].create(
                cargo_info_vals
            )

    ##########################
    # CT-e tag: compl
    ##########################

    cte40_xObs = fields.Text(compute="_compute_cte40_compl")
    cte40_obsCont = fields.One2many(
        "l10n_br_fiscal.comment", compute="_compute_cte40_obsCont"
    )

    cte40_obsFisco = fields.One2many(
        "l10n_br_fiscal.comment", compute="_compute_cte40_obsCont"
    )

    ##########################
    # CT-e tag: compl
    # Methods
    ##########################

    @api.depends("comment_ids")
    def _compute_cte40_obsCont(self):
        for doc in self.filtered(filter_processador_edoc_cte):
            doc.cte40_obsCont = doc.comment_ids.filtered(
                lambda c: c.comment_type == "commercial"
            )
            doc.cte40_obsFisco = doc.comment_ids.filtered(
                lambda c: c.comment_type == "fiscal"
            )

    def _compute_cte40_compl(self):
        for doc in self.filtered(filter_processador_edoc_cte):
            fiscal_data = (
                doc.fiscal_additional_data if doc.fiscal_additional_data else ""
            )
            customer_data = (
                doc.customer_additional_data if doc.customer_additional_data else ""
            )
            doc.cte40_xObs = (fiscal_data + " " + customer_data)[:256].strip()

    ##########################
    # CT-e tag: entrega
    ##########################

    # TODO: pensar em algo genericoom base nisso decidir quais tags
    # puxar (comData,semData,noPeriodo...)
    cte40_tpPer = fields.Selection(
        selection=COMDATA_TPPER, string="Tipo de data/período programado", default="2"
    )
    cte40_dProg = fields.Date("Data Programada", default=fields.Date.today)

    cte40_tpHor = fields.Selection(SEMHORA_TPHOR, string="Tipo de hora", default="0")

    ##########################
    # CT-e tag: emit
    ##########################

    cte40_emit = fields.Many2one(
        comodel_name="res.company",
        compute="_compute_cte_emit_data",
        string="Emit",
    )

    cte40_CRT = fields.Selection(
        related="company_id.tax_framework",
        string="Código de Regime Tributário (CTe)",
    )

    ##########################
    # CT-e tag: emit
    # Compute Methods
    ##########################

    @api.depends("partner_id", "company_id")
    def _compute_cte_emit_data(self):
        for doc in self:  # TODO if out
            doc.cte40_emit = doc.company_id

    def _set_cte40_IEST(self):
        self.ensure_one()
        iest = ""
        if self.partner_id:
            dest_state_id = self.partner_id.state_id
            if dest_state_id in self.company_id.state_tax_number_ids.mapped("state_id"):
                stn_id = self.company_id.state_tax_number_ids.filtered(
                    lambda stn: stn.state_id == dest_state_id
                )
                iest = stn_id.l10n_br_ie_code
                iest = re.sub("[^0-9]+", "", iest)
        self.company_l10n_br_ie_code_st = iest

    ##########################
    # CT-e tag: rem
    ##########################

    cte40_rem = fields.Many2one(
        comodel_name="res.partner",
        string="Remetente",
        related="partner_sendering_id",
    )

    ##########################
    # CT-e tag: exped
    ##########################

    cte40_exped = fields.Many2one(
        comodel_name="res.partner",
        string="Expedidor",
        related="partner_shippering_id",
    )

    ##########################
    # CT-e tag: dest
    ##########################

    cte40_dest = fields.Many2one(
        comodel_name="res.partner",
        string="Destinatário",
        related="partner_shipping_id",
    )

    ##########################
    # CT-e tag: receb
    ##########################

    cte40_receb = fields.Many2one(
        comodel_name="res.partner",
        string="Recebedor",
        related="partner_receivering_id",
    )

    ##########################
    # CT-e tag: vPrest
    ##########################

    cte40_vTPrest = fields.Monetary(related="amount_total")

    cte40_vRec = fields.Monetary(related="amount_price_gross")

    cte40_comp = fields.One2many(
        comodel_name="l10n_br_fiscal.document.line",
        inverse_name="document_id",
        related="fiscal_line_ids",
    )

    ##################################################
    # CT-e tag: ICMS
    # Grupo N01. Grupo Tributação do ICMS= 00
    # Grupo N02. Grupo Tributação do ICMS= 20
    # Grupo N03. Grupo Tributação do ICMS= 45 (40, 41 e 51)
    # Grupo N04. Grupo Tributação do ICMS= 60
    # Grupo N05. Grupo Tributação do ICMS= 90 - ICMS outros
    # Grupo N06. Grupo Tributação do ICMS= 90 - ICMS Outra UF
    # Grupo N06. Grupo Tributação do ICMS= 01 - ISSN
    #################################################

    cte40_vTotTrib = fields.Monetary(related="amount_estimate_tax")

    # TODO: Tratar
    # cte40_infAdFisco = fields.Text(related="additional_data")

    ##################################################
    # CT-e tag: ICMS
    # Methods
    ##################################################

    cte40_choice_icms = fields.Selection(
        selection=CTE_ICMS_SELECTION,
        string="Tipo de ICMS",
        compute="_compute_cte40_choice_icms",
        store=True,
    )

    cte40_CST = fields.Selection(
        selection=CTE_CST,
        string="Classificação Tributária do Serviço",
        compute="_compute_cte40_choice_icms",
        store=True,
    )

    # ICMSSN
    cte40_indSN = fields.Float(default=1)

    # # ICMSOutraUF
    # # TODO

    ##########################
    # CT-e tag: ICMS
    # Compute Methods
    ##########################

    @api.depends("fiscal_line_ids", "fiscal_line_ids.icms_cst_id")
    def _compute_cte40_choice_icms(self):
        for record in self.filtered(filter_processador_edoc_cte):
            record.cte40_choice_icms = None
            record.cte40_CST = None
            if not record.fiscal_line_ids:
                continue
            if record.fiscal_line_ids[0].icms_cst_id.code in ICMS_CST:
                if record.fiscal_line_ids[0].icms_cst_id.code in ["40", "41", "50"]:
                    record.cte40_choice_icms = "cte40_ICMS45"
                    record.cte40_CST = "45"
                elif (
                    record.fiscal_line_ids[0].icms_cst_id.code == "90"
                    and record.partner_id.state_id != record.company_id.state_id
                ):
                    record.cte40_choice_icms = "cte40_ICMSOutraUF"
                else:
                    record.cte40_choice_icms = "{}{}".format(
                        "cte40_ICMS", record.fiscal_line_ids[0].icms_cst_id.code
                    )
                    record.cte40_CST = record.fiscal_line_ids[0].icms_cst_id.code
            elif record.fiscal_line_ids[0].icms_cst_id.code in ICMS_SN_CST:
                record.cte40_choice_icms = "cte40_ICMSSN"
                record.cte40_CST = "90"

    def _export_fields_cte40_icms(self):
        # Verifica se fiscal_line_ids está vazio para evitar erros
        if not self.fiscal_line_ids:
            return {}

        # TODO:aprimorar. talvez criar os campos relacionados com os campos e totais
        # do documento fiscal e buscar apenas os percentuais da primeira linha
        first_line = self.fiscal_line_ids[0]

        icms = {
            "CST": self.cte40_CST,
            "vBC": 0.0,
            "pRedBC": first_line.icms_reduction,
            "pICMS": first_line.icms_percent,
            "vICMS": 0.0,
            "vICMSSubstituto": 0.0,
            "indSN": int(self.cte40_indSN),
            "vBCSTRet": 0.0,
            "vICMSSTRet": 0.0,
            "pICMSSTRet": first_line.icmsst_wh_percent,
        }

        for line in self.fiscal_line_ids:
            icms["vBC"] += line.icms_base
            icms["vICMS"] += line.icms_value
            icms["vICMSSubstituto"] += line.icms_substitute
            icms["vBCSTRet"] += line.icmsst_wh_base
            icms["vICMSSTRet"] += line.icmsst_wh_value

        # Formatar os valores acumulados
        icms["vBC"] = str("%.02f" % icms["vBC"])
        icms["vICMS"] = str("%.02f" % icms["vICMS"])
        icms["vICMSSubstituto"] = str("%.02f" % icms["vICMSSubstituto"])
        icms["vBCSTRet"] = str("%.02f" % icms["vBCSTRet"])
        icms["vICMSSTRet"] = str("%.02f" % icms["vICMSSTRet"])
        icms["pRedBC"] = str("%.04f" % icms["pRedBC"])
        icms["pICMS"] = str("%.02f" % icms["pICMS"])
        icms["pICMSSTRet"] = str("%.02f" % icms["pICMSSTRet"])

        return icms

    def _export_fields_cte_40_timp(self, xsd_fields, class_obj, export_dict):
        # TODO Not Implemented
        for record in self.filtered(filter_processador_edoc_cte):
            if "cte40_ICMSOutraUF" in xsd_fields:
                xsd_fields.remove("cte40_ICMSOutraUF")

            xsd_fields = [record.cte40_choice_icms]
            icms_tag = (
                record.cte40_choice_icms.replace("cte40_", "")
                .replace("ICMSSN", "Icmssn")
                .replace("ICMS", "Icms")
            )
            binding_module = sys.modules[record._get_spec_property("binding_module")]
            icms = binding_module.Timp
            icms_binding = getattr(icms, icms_tag)
            icms_dict = record._export_fields_cte40_icms()
            sliced_icms_dict = {
                key: icms_dict.get(key)
                for key in icms_binding.__dataclass_fields__.keys()
                if icms_dict.get(key)
            }
            export_dict[icms_tag.upper()] = icms_binding(**sliced_icms_dict)

    # ##########################
    # # CT-e tag: ICMSUFFim
    # ##########################

    # cte40_vBCUFFim = fields.Monetary(related="icms_destination_base")
    # cte40_pFCPUFFim = fields.Monetary(compute="_compute_cte40_ICMSUFFim", store=True)
    # cte40_pICMSUFFim = fields.Monetary(compute="_compute_cte40_ICMSUFFim", store=True)
    # # TODO
    # # cte40_pICMSInter = fields.Selection(
    # #    selection=[("0", "Teste")],
    # #    compute="_compute_cte40_ICMSUFFim")

    # def _compute_cte40_ICMSUFFim(self):
    #     for record in self:
    #         #    if record.icms_origin_percent:
    #         #        record.cte40_pICMSInter =
    #                       str("%.02f" % record.icms_origin_percent)
    #         #    else:
    #         #        record.cte40_pICMSInter = False

    #         record.cte40_pFCPUFFim = record.icmsfcp_percent
    #         record.cte40_pICMSUFFim = record.icms_destination_percent

    # cte40_vFCPUFfim = fields.Monetary(related="icmsfcp_value")
    # cte40_vICMSUFFim = fields.Monetary(related="icms_destination_value")
    # cte40_vICMSUFIni = fields.Monetary(related="icms_origin_value")

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

    # def _compute_cte40_infDoc(self):
    #     for doc in self:
    #         doc.cte40_infDoc = doc

    cte40_infCTeComp = fields.One2many(
        comodel_name="l10n_br_fiscal.document.related",
        inverse_name="document_id",
    )

    ##########################
    # CT-e tag: infCarga
    ##########################

    cte40_vCarga = fields.Monetary(
        string="Valor total da carga",
    )

    cte40_proPred = fields.Char(
        string="Produto predominante",
    )

    cte40_xOutCat = fields.Char(
        string="Outras características da carga",
    )

    cte40_infQ = fields.One2many(
        comodel_name="l10n_br_cte.cargo.quantity.infos",
        inverse_name="document_id",
        compute="_compute_cte40_infQ",
        readonly=False,
        store=True,
    )

    cte40_vCargaAverb = fields.Monetary(
        string="Valor da Carga para efeito de averbação",
    )

    ##########################
    # CT-e tag: infDoc
    ##########################

    cte40_infDoc = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        compute="_compute_cte40_infDoc",
        string="Informações dos documentos transportados",
    )

    def _compute_cte40_infDoc(self):
        for doc in self.filtered(filter_processador_edoc_cte):
            doc.cte40_infDoc = doc

    def _compute_cte40_infNFe(self):
        for record in self.filtered(filter_processador_edoc_cte):
            record.cte40_infNFe = record.document_related_ids.filtered(
                lambda r: r.cte40_infDoc == "cte40_infNFe"
            )

    def _compute_cte40_infOutros(self):
        for record in self.filtered(filter_processador_edoc_cte):
            record.cte40_infOutros = record.document_related_ids.filtered(
                lambda r: r.cte40_infDoc == "cte40_infOutros"
            )

    cte40_infNFe = fields.One2many(
        comodel_name="l10n_br_fiscal.document.related",
        inverse_name="document_id",
        string="Informações das NF-e DOCS (Cte)",
        compute="_compute_cte40_infNFe",
    )

    cte40_infOutros = fields.One2many(
        comodel_name="l10n_br_fiscal.document.related",
        inverse_name="document_id",
        string="Informações dos Outros DOCS (Cte)",
        compute="_compute_cte40_infOutros",
    )

    ##########################
    # CT-e tag: veicNovos
    ##########################

    cte40_veicNovos = fields.One2many(
        comodel_name="l10n_br_cte.transported.vehicles",
        inverse_name="document_id",
    )

    ##########################
    # CT-e tag: autXML
    # Compute Methods
    ##########################

    def _default_cte40_autxml(self):
        company = self.env.company
        authorized_partners = []
        if company.accountant_id:
            authorized_partners.append(company.accountant_id.id)
        if company.technical_support_id:
            authorized_partners.append(company.technical_support_id.id)
        return authorized_partners

    ##########################
    # CT-e tag: autXML
    ##########################

    cte40_autXML = fields.One2many(default=_default_cte40_autxml)

    ##########################
    # CT-e tag: infCTeSupl
    ##########################

    cte40_infCTeSupl = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.supplement",
    )

    ##########################
    # CT-e tag: infRespTec
    ##########################

    cte40_infRespTec = fields.Many2one(
        comodel_name="res.partner",
        related="company_id.technical_support_id",
    )

    ##########################
    # CT-e tag: infmodal
    ##########################

    cte40_modal = fields.Selection(related="transport_modal")

    cte_modal = fields.Selection(related="transport_modal")

    cte40_versaoModal = fields.Char(default=CTE_MODAL_VERSION_DEFAULT)

    # Campos do Modal Aereo
    cte_modal_aereo_id = fields.Many2one(comodel_name="l10n_br_cte.modal.aereo")

    cte40_nMinu = fields.Char(
        string="Número da Minuta",
        help=(
            "Número da Minuta\nDocumento que precede o CT-e, assinado pelo "
            "expedidor, espécie de pedido de serviço"
        ),
    )

    cte40_nOCA = fields.Char(
        string="Número Operacional do Conhecimento Aéreo",
        help=(
            "Número Operacional do Conhecimento Aéreo\nRepresenta o número de "
            "controle comumente utilizado pelo conhecimento aéreo composto por"
            " uma sequência numérica de onze dígitos. Os três primeiros "
            "dígitos representam um código que os operadores de transporte "
            "aéreo associados à IATA possuem. Em seguida um número de série de"
            " sete dígitos determinados pelo operador de transporte aéreo. "
            "Para finalizar, um dígito verificador, que é um sistema de módulo"
            " sete imponderado o qual divide o número de série do conhecimento"
            " aéreo por sete e usa o resto como dígito de verificação."
        ),
    )

    cte40_dPrevAereo = fields.Date(
        string="Data prevista da entrega",
        help="Data prevista da entrega\nFormato AAAA-MM-DD",
    )

    cte40_xDime = fields.Char(
        string="Dimensão",
        help=(
            "Dimensão\nFormato:1234X1234X1234 (cm). Esse campo deve sempre que"
            " possível ser preenchido. Entretanto, quando for impossível o "
            "preenchimento das dimensões, fica obrigatório o preenchimento da "
            "cubagem em metro cúbico do leiaute do CT-e da estrutura genérica "
            "(infQ)."
        ),
    )

    # TODO: Tratar
    # def _compute_cte40_dime(self):
    #     for record in self:
    #         for package in record.product_id.packaging_ids:
    #             record.cte40_xDime = (
    #                 package.width + "X" + package.packaging_length +
    #                 "X" + package.width
    #             )

    cte40_CL = fields.Char(
        string="Classe",
        help=(
            "Classe\nPreencher com:\n\t\t\t\t\t\t\t\t\tM - Tarifa "
            "Mínima;\n\t\t\t\t\t\t\t\t\tG - Tarifa Geral;\n\t\t\t\t\t\t\t\t\tE"
            " - Tarifa Específica"
        ),
    )

    cte40_cTar = fields.Char(
        string="Código da Tarifa",
        help=(
            "Código da Tarifa\nDeverão ser incluídos os códigos de três "
            "dígitos, correspondentes à tarifa."
        ),
    )
    # Existem dois vTar no spec, um float e um monetary, por isso a mudança de nome
    cte40_aereo_vTar = fields.Monetary(
        string="Valor da Tarifa",
        currency_field="brl_currency_id",
        help="Valor da Tarifa\nValor da tarifa por kg quando for o caso.",
    )

    cte40_peri = fields.One2many(
        comodel_name="l10n_br_cte.modal.aereo.peri",
        inverse_name="document_id",
        string="Dados de carga perigosa",
    )

    # Campos do Modal Aquaviario
    cte_modal_aquaviario_id = fields.Many2one(comodel_name="l10n_br_cte.modal.aquav")

    # TODO: Tratar
    # cte40_vPrest = fields.Monetary(
    #     compute="_compute_cte40_vPrest",  # FIX
    #     store=True,
    #     string="Valor da Prestação Base de Cálculo",
    # )

    cte40_vAFRMM = fields.Monetary(
        string="AFRMM",
        currency_field="brl_currency_id",
        help=("AFRMM (Adicional de Frete para Renovação da Marinha Mercante)"),
    )

    cte40_xNavio = fields.Char(string="Identificação do Navio")

    cte40_nViag = fields.Char(string="Número da Viagem")

    cte40_direc = fields.Selection(
        selection=[
            ("N", "Norte, L-Leste, S-Sul, O-Oeste"),
            ("S", "Sul, O-Oeste"),
            ("L", "Leste, S-Sul, O-Oeste"),
            ("O", "Oeste"),
        ],
        string="Direção",
        help="Direção\nPreencher com: N-Norte, L-Leste, S-Sul, O-Oeste",
    )

    cte40_irin = fields.Char(
        string="Irin do navio",
        help="Irin do navio sempre deverá ser informado",
    )

    cte40_tpNav = fields.Selection(
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

    cte40_balsa = fields.One2many(
        comodel_name="l10n_br_cte.modal.aquav.balsa",
        inverse_name="document_id",
        string="Grupo de informações das balsas",
    )

    # Campos do Modal Dutoviario
    cte_modal_dutoviario_id = fields.Many2one(comodel_name="l10n_br_cte.modal.duto")

    cte40_dIni = fields.Date(string="Data de Início da prestação do serviço")

    cte40_dFim = fields.Date(string="Data de Fim da prestação do serviço")

    cte40_vTar = fields.Float(string="Valor da tarifa")

    # Campos do Modal Ferroviario
    cte_modal_ferroviario_id = fields.Many2one(comodel_name="l10n_br_cte.modal.ferrov")

    cte40_tpTraf = fields.Selection(
        selection=FERROV_TPTRAF,
        default="0",
        string="Tipo de Tráfego",
    )

    cte40_fluxo = fields.Char(
        string="Fluxo Ferroviário",
        help=(
            "Fluxo Ferroviário\nTrata-se de um número identificador do "
            "contrato firmado com o cliente"
        ),
    )

    cte40_pass = fields.Char(
        string="Fluxo Pass",
    )

    cte40_vFrete = fields.Monetary(
        related="amount_freight_value",
        string="Valor do Frete do Tráfego Mútuo",
        currency_field="brl_currency_id",
    )

    cte40_respFat = fields.Selection(
        TRAFMUT_RESPFAT,
        string="Responsável pelo Faturamento",
    )

    cte40_ferrEmi = fields.Selection(
        TRAFMUT_FERREMI,
        string="Ferrovia Emitente do CTe",
        help=(
            "Ferrovia Emitente do CTe\nPreencher com: "
            "\n\t\t\t\t\t\t\t\t\t1-Ferrovia de origem; "
            "\n\t\t\t\t\t\t\t\t\t2-Ferrovia de destino"
        ),
    )

    cte40_chCTeFerroOrigem = fields.Char(
        string="Chave de acesso do CT-e emitido",
        help="Chave de acesso do CT-e emitido pelo ferrovia de origem",
    )

    cte40_ferroEnv = fields.Many2many(
        comodel_name="res.partner",
        string="Informações das Ferrovias Envolvidas",
    )

    # Campos do Modal rodoviario
    cte_modal_rodoviario_id = fields.Many2one(comodel_name="l10n_br_cte.modal.rodo")

    cte40_RNTRC = fields.Char(
        string="RNTRC",
        help="Registro Nacional de Transportadores Rodoviários de Carga",
        compute="_compute_cte40_RNTRC",
        store=True,
    )

    @api.depends(
        "issuer",
        "company_id",
        "company_id.partner_id.rntrc_code",
        "partner_id",
        "partner_id.rntrc_code",
    )
    def _compute_cte40_RNTRC(self):
        for record in self.filtered(filter_processador_edoc_cte):
            record.cte40_RNTRC = None
            if record.issuer == DOCUMENT_ISSUER_COMPANY and record.company_id:
                record.cte40_RNTRC = record.company_id.partner_id.rntrc_code
            elif record.partner_id:
                record.cte40_RNTRC = record.partner_id.rntrc_code

    cte40_occ = fields.One2many(
        comodel_name="l10n_br_cte.modal.rodo.occ",
        inverse_name="document_id",
        string="Ordens de Coleta associados",
        copy=False,
    )

    ##########################
    # CT-e tag: infmodal
    # Compute Methods
    ##########################

    def _export_fields_cte_40_tcte_infmodal(self, xsd_fields, class_obj, export_dict):
        if self.cte40_modal == "01":
            export_dict["any_element"] = self._export_cte_modal_rodoviario()
        elif self.cte40_modal == "02":
            export_dict["any_element"] = self._export_cte_modal_aereo()
        elif self.cte40_modal == "03":
            export_dict["any_element"] = self._export_cte_modal_aquaviario()
        elif self.cte40_modal == "04":
            export_dict["any_element"] = self._export_cte_modal_ferroviario()
        elif self.cte40_modal == "05":
            export_dict["any_element"] = self._export_cte_modal_dutoviario()

    def _export_cte_modal_aereo(self):
        if not self.cte_modal_aereo_id:
            self.cte_modal_aereo_id = self.cte_modal_aereo_id.create(
                {"document_id": self.id}
            )

        return self.cte_modal_aereo_id._build_binding("cte", "40")

    def _export_cte_modal_ferroviario(self):
        if not self.cte_modal_ferroviario_id:
            self.cte_modal_ferroviario_id = self.cte_modal_ferroviario_id.create(
                {"document_id": self.id}
            )

        return self.cte_modal_ferroviario_id._build_binding("cte", "40")

    def _export_cte_modal_aquaviario(self):
        if not self.cte_modal_aquaviario_id:
            self.cte_modal_aquaviario_id = self.cte_modal_aquaviario_id.create(
                {"document_id": self.id}
            )

        return self.cte_modal_aquaviario_id._build_binding("cte", "40")

    def _export_cte_modal_rodoviario(self):
        if not self.cte_modal_rodoviario_id:
            self.cte_modal_rodoviario_id = self.cte_modal_rodoviario_id.create(
                {"document_id": self.id}
            )

        return self.cte_modal_rodoviario_id._build_binding("cte", "40")

    def _export_cte_modal_dutoviario(self):
        if not self.cte_modal_dutoviario_id:
            self.cte_modal_dutoviario_id = self.cte_modal_dutoviario_id.create(
                {"document_id": self.id}
            )

        return self.cte_modal_dutoviario_id._build_binding("cte", "40")

    ################################
    # Framework Spec model's methods
    ################################

    def _export_field(self, xsd_field, class_obj, member_spec, export_value=None):
        if xsd_field == "cte40_tpAmb":
            self.env.context = dict(self.env.context)
            self.env.context.update({"tpAmb": self[xsd_field]})
            self.env.context.update({"doc": self.id})

        # TODO: Força a remoção da tag infGlobalizado já que o
        # campo xObs está no l10n_br_fiscal.document
        if xsd_field == "cte40_infGlobalizado":
            return False
        if xsd_field == "cte40_toma4" and self.cte40_choice_toma == "cte40_toma3":
            return False
        elif xsd_field == "cte40_toma3" and self.cte40_choice_toma == "cte40_toma4":
            return False
        return super()._export_field(xsd_field, class_obj, member_spec, export_value)

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        """
        Overriden to avoid creating inner tag for m2o if none of the
        denormalized inner attribute has been set.
        """
        self.ensure_one()
        if field_name in self._get_stacking_points().keys():
            if field_name == "cte40_ISSQNtot" and not any(
                t == "issqn"
                for t in self.cte40_det.mapped("product_id.tax_icms_or_issqn")
            ):
                return False

            elif (not xsd_required) and field_name not in ["cte40_enderDest"]:
                comodel = self.env[
                    self._get_stacking_points().get(field_name).comodel_name
                ]
                fields = [
                    f
                    for f in comodel._fields
                    if f.startswith(self._spec_prefix())
                    and f in self._fields.keys()
                    and f
                    # don't try to cte40_fat id when reading cte40_cobr for instance
                    not in self._get_stacking_points().keys()
                ]
                sub_tag_read = self.read(fields)[0]
                if not any(
                    v
                    for k, v in sub_tag_read.items()
                    if k.startswith(self._spec_prefix())
                ):
                    return False

        if (
            field_name == "cte40_emit"
            and self.fiscal_operation_type == "out"
            and self.issuer == "company"
        ):
            self._set_cte40_IEST()
            res = super()._export_many2one(field_name, xsd_required, class_obj)
            if self.company_l10n_br_ie_code_st:
                res.IEST = self.company_l10n_br_ie_code_st
            return res

        return super()._export_many2one(field_name, xsd_required, class_obj)

    @api.model
    def _prepare_import_dict(
        self, values, model=None, parent_dict=None, defaults_model=None
    ):
        return {
            **super()._prepare_import_dict(values, model, parent_dict, defaults_model),
            "imported_document": True,
        }

    def _build_attr(self, node, fields, vals, path, attr):
        key = f"cte40_{attr[0]}"  # TODO schema wise
        value = getattr(node, attr[0])

        # if attr[0] == "any_element":  # build modal
        #     modal_id = self._get_modal_to_build(node.any_element.__module__)
        #     if modal_id is False:
        #         return

        #     modal_attrs = modal_id.build_attrs(value, path=path)
        #     for chave, valor in modal_attrs.items():
        #         vals[chave] = valor
        #     return

        if key == "cte40_mod":
            if isinstance(value, Enum):
                value = value.value

            vals["document_type_id"] = (
                self.env["l10n_br_fiscal.document.type"]
                .search([("code", "=", value)], limit=1)
                .id
            )

        return super()._build_attr(node, fields, vals, path, attr)

    def _build_many2one(self, comodel, vals, new_value, key, value, path):
        if key == "cte40_emit" and self.env.context.get("edoc_type") == "in":
            enderEmit_value = self.env["res.partner"].build_attrs(
                value.enderEmit, path=path
            )
            new_value.update(enderEmit_value)
            company_cnpj = self.env.company.cnpj_cpf.translate(
                str.maketrans("", "", string.punctuation)
            )
            emit_cnpj = new_value.get("cte40_CNPJ").translate(
                str.maketrans("", "", string.punctuation)
            )
            if company_cnpj != emit_cnpj:
                vals["issuer"] = "partner"
            new_value["is_company"] = True
            new_value["cnpj_cpf"] = emit_cnpj
            super()._build_many2one(
                self.env["res.partner"], vals, new_value, "partner_id", value, path
            )
        elif key == "cte40_dest" and self.env.context.get("edoc_type") == "out":
            enderDest_value = self.env["res.partner"].build_attrs(
                value.enderDest, path=path
            )
            new_value.update(enderDest_value)
            company_cnpj = self.env.company.cnpj_cpf.translate(
                str.maketrans("", "", string.punctuation)
            )
            dest_cnpj = new_value.get("cte40_CNPJ").translate(
                str.maketrans("", "", string.punctuation)
            )
            if company_cnpj != dest_cnpj:
                vals["issuer"] = "partner"
            new_value["is_company"] = True
            new_value["cnpj_cpf"] = dest_cnpj
            super()._build_many2one(
                self.env["res.partner"], vals, new_value, "partner_id", value, path
            )
        elif (
            self.env.context.get("edoc_type") == "in"
            and key
            in [
                "cte40_dest",
                "cte40_enderDest",
            ]
        ) or (
            self.env.context.get("edoc_type") == "out"
            and key
            in [
                "cte40_emit",
                "cte40_enderEmit",
            ]
        ):
            # this would be the emit/company data, but we won't update it on
            # CTe import so just do nothing
            return
        elif (
            self._name == "account.invoice"
            and comodel._name == "l10n_br_fiscal.document"
        ):
            # module l10n_br_account_nfe
            # stacked m2o
            vals.update(new_value)
        else:
            super()._build_many2one(comodel, vals, new_value, key, value, path)

    @api.model
    def _get_concrete_model(self, model_name):
        result = super()._get_concrete_model(model_name)
        if self._module == "l10n_br_cte" and not result:
            model_type = model_name.split(".")[-1]
            model_name = model_name.rpartition(".")[0] + ".tcte_" + model_type
            result = super()._get_concrete_model(model_name)
        return result

    ################################
    # Business Model Methods
    ################################

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.with_context(lang="pt_BR").filtered(
            filter_processador_edoc_cte
        ):
            inf_cte = record._build_binding("cte", "40")

            inf_cte_supl = None
            if record.cte40_infCTeSupl:
                inf_cte_supl = record.cte40_infCTeSupl._build_binding("cte", "40")

            cte = Cte(infCte=inf_cte, infCTeSupl=inf_cte_supl, signature=None)
            edocs.append(cte)
        return edocs

    # def _edoc_processor(self):
    #     if self.document_type != MODELO_FISCAL_CTE:
    #         return super()._edoc_processor()

    #     if not self.company_id.certificate_nfe_id:
    #         raise UserError(_("Certificado não encontrado"))

    #     certificado = self.env.company._get_br_ecertificate()
    #     session = Session()
    #     session.verify = False

    #     params = {
    #         "transmissao": TransmissaoCTE(certificado, session),
    #         "uf": self.company_id.state_id.ibge_code,
    #         "versao": self.cte_version,
    #         "ambiente": self.cte_environment,
    #     }
    #     return edoc_cte(**params)

    def _edoc_processor(self):
        pass

    def _document_export(self, pretty_print=True):
        result = super()._document_export()
        for record in self.filtered(filter_processador_edoc_cte):
            edoc = record.serialize()[0]
            # processador = record._edoc_processor()
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

            # xml_assinado = processador.assina_raiz(edoc, edoc.infCte.Id)
            # self._validate_xml(xml_assinado)
        return result

    def _validate_xml(self, xml_file):
        self.ensure_one()

        if not self.filtered(filter_processador_edoc_cte):
            return super()._validate_xml(xml_file)

        erros = Cte.schema_validation(xml_file)
        erros = "\n".join(erros)
        self.write({"xml_error_message": erros or False})

    def update_status_cte(self, process):
        self.ensure_one()

        if hasattr(process, "protocolo"):
            infProt = process.protocolo.infProt
        else:
            infProt = process.resposta.protCTe.infProt

        if infProt.cStat in AUTORIZADO:
            state = SITUACAO_EDOC_AUTORIZADA
            self._cte_response_add_proc(process)
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
                file_response_xml=process.processo_xml.decode("utf-8"),
            )
        self.write(
            {
                "status_code": infProt.cStat,
                "status_name": infProt.xMotivo,
            }
        )
        self._change_state(state)

    def _eletronic_document_send(self):
        super()._eletronic_document_send()
        for record in self.filtered(filter_processador_edoc_cte):
            if record.xml_error_message:
                return
            processador = record._edoc_processor()
            for edoc in record.serialize():
                process = None
                for p in processador.processar_documento(edoc):
                    process = p
                    if process.webservice in ["cteRecepcaoLote", "cteRecepcao"]:
                        send_xml = gzip.decompress(
                            base64.b64decode(process.envio_xml)
                        ).decode("utf-8")
                        record.authorization_event_id._save_event_file(send_xml, "xml")

            if process.resposta.cStat in LOTE_PROCESSADO + ["100"]:
                record.update_status_cte(process)

            elif process.resposta.cStat in DENEGADO:
                record._change_state(SITUACAO_EDOC_DENEGADA)
                record.write(
                    {
                        "status_code": process.resposta.cStat,
                        "status_name": process.resposta.xMotivo,
                    }
                )

            else:
                record._change_state(SITUACAO_EDOC_REJEITADA)
                record.write(
                    {
                        "status_code": process.resposta.cStat,
                        "status_name": process.resposta.xMotivo,
                    }
                )

    def _document_cancel(self, justificative):
        result = super()._document_cancel(justificative)
        online_event = self.filtered(filter_processador_edoc_cte)
        if online_event:
            online_event._cte_cancel()
        return result

    def _cte_cancel(self):
        self.ensure_one()
        processador = self._edoc_processor()

        if not self.authorization_protocol:
            raise UserError(_("Authorization Protocol Not Found!"))

        evento = processador.cancela_documento(
            chave=self.document_key,
            protocolo_autorizacao=self.authorization_protocol,
            justificativa=self.cancel_reason.replace("\n", "\\n"),
        )
        process = processador.enviar_lote_evento(lista_eventos=[evento])

        self.cancel_event_id = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=(EVENT_ENV_PROD if self.cte40_tpAmb == "1" else EVENT_ENV_HML),
            event_type="2",
            xml_file=process.envio_xml,
            document_id=self,
        )

        resposta = process.resposta.infEvento

        if resposta.cStat not in CANCELADO:
            mensagem = "Erro no cancelamento"
            mensagem += "\nCódigo: " + resposta.cStat
            mensagem += "\nMotivo: " + resposta.xMotivo
            raise UserError(mensagem)

        if resposta.chCTe == self.document_key:
            if resposta.cStat in CANCELADO_FORA_PRAZO:
                self.state_fiscal = SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO
            elif resposta.cStat in CANCELADO_DENTRO_PRAZO:
                self.state_fiscal = SITUACAO_FISCAL_CANCELADO

            self.state_edoc = SITUACAO_EDOC_CANCELADA
            self.cancel_event_id.set_done(
                status_code=resposta.cStat,
                response=resposta.xMotivo,
                protocol_date=fields.Datetime.to_string(
                    datetime.fromisoformat(resposta.dhRegEvento)
                ),
                protocol_number=resposta.nProt,
                file_response_xml=process.retorno.content.decode("utf-8"),
            )

    def _document_correction(self, justificative):
        result = super()._document_correction(justificative)
        online_event = self.filtered(filter_processador_edoc_cte)
        if online_event:
            online_event._cte_correction(justificative)
        return result

    def _cte_correction(self, justificative):
        self.ensure_one()
        processador = self._edoc_processor()

        numeros = self.event_ids.filtered(
            lambda e: e.type == "14" and e.state == "done"
        ).mapped("sequence")

        sequence = str(int(max(numeros)) + 1) if numeros else "1"

        evento = processador.carta_correcao(
            chave=self.document_key,
            protocolo_autorizacao=self.authorization_protocol,
            justificativa=justificative.replace("\n", "\\n"),
            sequencia=sequence,
        )
        process = processador.enviar_lote_evento(lista_eventos=[evento])
        # Gravamos o arquivo no disco e no filestore ASAP.
        event_id = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=(EVENT_ENV_PROD if self.cte40_tpAmb == "1" else EVENT_ENV_HML),
            event_type="14",
            xml_file=process.envio_xml,
            document_id=self,
            sequence=sequence,
            justification=justificative,
        )

        resposta = process.resposta.infEvento

        if resposta.cStat not in EVENTO_RECEBIDO and not (
            resposta.chCTe == self.document_key
        ):
            mensagem = "Erro na carta de correção"
            mensagem += "\nCódigo: " + resposta.cStat
            mensagem += "\nMotivo: " + resposta.xMotivo
            raise UserError(mensagem)

        event_id.set_done(
            status_code=resposta.cStat,
            response=resposta.xMotivo,
            protocol_date=fields.Datetime.to_string(
                datetime.fromisoformat(resposta.dhRegEvento)
            ),
            protocol_number=resposta.nProt,
            file_response_xml=process.retorno.content.decode("utf-8"),
        )

    # def _document_qrcode(self):
    #     super()._document_qrcode()

    #     for record in self.filtered(filter_processador_edoc_cte):
    #         record.cte40_infCTeSupl = self.env[
    #             "l10n_br_fiscal.document.supplement"
    #         ].create(
    #             {
    #                 "qrcode": record.get_cte_qrcode(),
    #             }
    #         )

    def get_cte_qrcode(self):
        if self.document_type != MODELO_FISCAL_CTE:
            return
        processador = self._edoc_processor()
        return processador.monta_qrcode(self.document_key)

    def _need_compute_cte_tags(self):
        if (
            self.state_edoc in [SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_A_ENVIAR]
            and self.processador_edoc == PROCESSADOR_OCA
            and self.document_type_id.code in ["57"]
            and self.issuer == DOCUMENT_ISSUER_COMPANY
        ):
            return True
        else:
            return False

    def _cte_response_add_proc(self, ws_response_process):
        """
        Inject the final NF-e, tag `cteProc`, into the response.
        """
        xml_soap = ws_response_process.retorno.content
        tree_soap = etree.fromstring(xml_soap)
        prot_element = tree_soap.xpath("//cte:protCTe", namespaces=CTE_XML_NAMESPACE)[0]
        proc_xml = self._cte_create_proc(prot_element)
        if proc_xml:
            # it is not always possible to create cteProc.
            parser = XmlParser()
            proc = parser.from_string(proc_xml.decode(), CteProc)
            ws_response_process.processo = proc
            ws_response_process.processo_xml = proc_xml

    def _cte_create_proc(self, prot_element):
        """
        Create the `cteProc` XML by combining the CT-e and the authorization protocol.

        This method decodes the saved `enviCTe` message, extracts the CTe> tag,
        and combines it with the provided authorization protocol element to create
        the `cteProc` XML, which represents the finalized CT-e document.

        Args:
            prot_element: The XML element containing the authorization protocol.

        Returns:
            The assembled `cteProc` XML, or None if the `send_file_id` data is not
            found.

        Note:
            Useful for recreating the final CT-e XML, as SEFAZ does not provide the
            complete XML upon consultation, only the authorization protocol.
        """
        self.ensure_one()

        if not self.send_file_id.datas:
            _logger.info(
                "CT-e data not found when trying to assemble the "
                "xml with the authorization protocol (cteProc)"
            )
            return None

        processor = self._edoc_processor()

        # Extract the <CTe> tag from the `enviCTe` message, which represents the CT-e
        xml_send = base64.b64decode(self.send_file_id.datas)
        tree_send = etree.fromstring(xml_send)
        doc_element = tree_send.xpath("//cte:CTe", namespaces=CTE_XML_NAMESPACE)[0]

        # Assemble the `cteProc` using the erpbrasil.edoc library.
        proc_xml = processor.monta_cte_proc(doc=doc_element, prot=prot_element)

        return proc_xml

    def import_binding_cte(self, binding, edoc_type="out"):
        document = (
            self.env["cte.40.tcte_infcte"]
            .with_context(tracking_disable=True, edoc_type=edoc_type, dry_run=False)
            .build_from_binding("cte", "40", binding.CTe.infCte)
        )

        if edoc_type == "in" and document.company_id.cnpj_cpf != cnpj_cpf.formata(
            binding.CTe.infCte.emit.CNPJ
        ):
            document.fiscal_operation_type = "in"
            document.issuer = "partner"

        return document

    def _document_number(self):
        # TODO: Criar campos no fiscal para codigo aleatorio e digito verificador,
        # pois outros modelos também precisam dessescampos: CT-e, MDF-e etc
        result = super()._document_number()
        for record in self.filtered(filter_processador_edoc_cte):
            if record.document_key:
                try:
                    chave = ChaveEdoc(record.document_key)
                    record.cte40_cCT = chave.codigo_aleatorio
                    record.cte40_cDV = chave.digito_verificador
                except Exception as e:
                    raise ValidationError(
                        _(
                            "%(name)s:\n %(error)s",
                            name=record.document_type_id.name,
                            error=e,
                        )
                    ) from e
        return result

    def make_pdf(self):
        if not self.filtered(filter_processador_edoc_cte):
            return super().make_pdf()

        attachment_data = {
            "name": self.document_key + ".pdf",
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/pdf",
            "type": "binary",
        }
        report = self.env.ref("l10n_br_cte.main_template_dacte")
        pdf_data = report._render_qweb_pdf(
            "main_template_dacte", self.fiscal_line_ids.document_id.ids
        )
        attachment_data["datas"] = base64.b64encode(pdf_data[0])
        file_pdf = self.file_report_id
        self.file_report_id = False
        file_pdf.unlink()

        self.file_report_id = self.env["ir.attachment"].create(attachment_data)
