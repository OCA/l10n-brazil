# Copyright 2023 KMEE
# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging
import re
import string
from datetime import datetime
from unicodedata import normalize

import erpbrasil.edoc.mdfe as _edoc_mdfe_mod
from erpbrasil.base.fiscal import cnpj_cpf
from erpbrasil.base.fiscal.edoc import ChaveEdoc
from erpbrasil.base.misc import punctuation_rm
from erpbrasil.edoc.mdfe import TransmissaoMDFE
from lxml import etree
from nfelib.mdfe.bindings.v3_0.mdfe_v3_00 import Mdfe
from nfelib.mdfe.bindings.v3_0.proc_mdfe_v3_00 import MdfeProc
from nfelib.nfe.ws.edoc_legacy import MDFeAdapter as edoc_mdfe
from requests import Session
from xsdata.formats.dataclass.parsers import XmlParser

from odoo import Command, _, api, fields
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    AUTORIZADO,
    CANCELADO,
    CANCELADO_DENTRO_PRAZO,
    CANCELADO_FORA_PRAZO,
    DENEGADO,
    DOCUMENT_ISSUER_COMPANY,
    ENCERRADO,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    LOTE_PROCESSADO,
    MODELO_FISCAL_MDFE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_ENCERRADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
)
from odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_modal_aquaviario_v3_00 import (
    AQUAV_TPNAV,
)
from odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_modal_rodoviario_v3_00 import (
    TUF,
    VALEPED_CATEGCOMBVEIC,
    VEICTRACAO_TPCAR,
    VEICTRACAO_TPROD,
)
from odoo.addons.spec_driven_model.models import spec_models

from ..constants.mdfe import (
    MDFE_EMISSION_PROCESS_DEFAULT,
    MDFE_EMISSION_PROCESSES,
    MDFE_EMIT_TYPES,
    MDFE_ENVIRONMENTS,
    MDFE_TRANSMISSIONS,
    MDFE_TRANSP_TYPE,
    MDFE_TRANSP_TYPE_DEFAULT,
)
from ..constants.modal import (
    MDFE_MODAL_DEFAULT,
    MDFE_MODAL_DEFAULT_AIRCRAFT,
    MDFE_MODAL_HARBORS,
    MDFE_MODAL_SHIP_TYPES,
    MDFE_MODAL_VERSION_DEFAULT,
    MDFE_MODALS,
)

# Ensure all states are supported in MDFe SVRS_STATES
_edoc_mdfe_mod.SVRS_STATES = tuple(
    state for state in _edoc_mdfe_mod.SIGLA_ESTADO if state != "AN"
)

MDFE_XML_NAMESPACE = {"mdfe": "http://www.portalfiscal.inf.br/mdfe"}

_logger = logging.getLogger(__name__)


def filtered_processador_edoc_mdfe(record):
    return (
        record.processador_edoc == PROCESSADOR_OCA
        and record.document_type_id.code == MODELO_FISCAL_MDFE
    )


class MDFe(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "mdfe.30.tmdfe_infmdfe"]
    _mdfe30_odoo_module = (
        "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_tipos_basico_v3_00"
    )
    _mdfe30_stacking_mixin = "mdfe.30.tmdfe_infmdfe"
    # all m2o at this level will be stacked even if not required:
    _mdfe30_stacking_force_paths = [
        "infmdfe.infAdic",
        "infmdfe.tot",
        "infmdfe.tmdfe_infsolicnff",
        "infmdfe.InfDoc",
    ]
    _mdfe_search_keys = ["mdfe30_Id"]

    # When dynamic stacking is applied the MDFe structure is:
    INFMDFE_TREE = """
> <tmdfe_infmdfe>
    > <ide>
        ≡ <infMunCarrega>
        ≡ <infPercurso>
    - <emit> res.company
    > <infModal>
    > <infDoc>
        ≡ <infMunDescarga> l10n_br_mdfe.municipio.descarga
    ≡ <seg> l10n_br_mdfe.seguro.carga
    - <prodPred> product.product
    > <tot>
    ≡ <lacres>
    ≡ <autXML> res.partner
    > <infAdic>
    - <infRespTec> res.partner
    - <infSolicNFF>
    - <infPAA>"""

    mdfe_version = fields.Selection(
        string="MDF-e Version",
        related="company_id.mdfe_version",
        readonly=False,
    )

    mdfe_environment = fields.Selection(
        string="MDF-e Environment",
        related="company_id.mdfe_environment",
        readonly=False,
    )

    ##########################
    # MDF-e spec related fields
    ##########################

    ##########################
    # MDF-e tag: infMDFe
    ##########################

    mdfe30_versao = fields.Char(compute="_compute_mdfe_version")

    mdfe30_Id = fields.Char(
        compute="_compute_mdfe30_id_tag",
        inverse="_inverse_mdfe30_id_tag",
    )

    ##########################
    # MDF-e tag: infMDFe
    # Methods
    ##########################

    @api.depends("mdfe_version")
    def _compute_mdfe_version(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_versao = record.mdfe_version

    @api.depends("document_type_id", "document_key")
    def _compute_mdfe30_id_tag(self):
        """Set schema data which are not just related fields"""

        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_Id = False

            if (
                record.document_type_id
                and record.document_type_id.prefix
                and record.document_key
            ):
                record.mdfe30_Id = (
                    f"{record.document_type_id.prefix}{record.document_key}"
                )

    def _inverse_mdfe30_id_tag(self):
        for record in self:
            if record.mdfe30_Id:
                record.document_key = re.findall(r"\d+", str(record.mdfe30_Id))[0]

    ##########################
    # MDF-e tag: ide
    ##########################

    mdfe30_cUF = fields.Selection(
        compute="_compute_mdfe30_uf", inverse="_inverse_mdfe30_uf"
    )

    mdfe30_tpAmb = fields.Selection(related="mdfe_environment")

    mdfe_environment = fields.Selection(
        selection=MDFE_ENVIRONMENTS,
        string="Environment",
        copy=False,
        default=lambda self: self.env.company.mdfe_environment,
    )

    mdfe30_tpEmit = fields.Selection(related="mdfe_emit_type")

    mdfe_emit_type = fields.Selection(
        selection=MDFE_EMIT_TYPES,
        string="Emit Type",
        copy=False,
        default=lambda self: self.env.company.mdfe_emit_type,
    )

    mdfe30_tpTransp = fields.Selection(related="mdfe_transp_type")

    mdfe_transp_type = fields.Selection(
        selection=MDFE_TRANSP_TYPE,
        string="Transp Type",
        copy=False,
        default=MDFE_TRANSP_TYPE_DEFAULT,
    )

    mdfe30_mod = fields.Char(related="document_type_id.code")

    mdfe30_serie = fields.Char(related="document_serie")

    mdfe30_nMDF = fields.Char(related="document_number")

    mdfe30_dhEmi = fields.Datetime(related="document_date")

    mdfe30_modal = fields.Selection(related="mdfe_modal")

    mdfe_modal = fields.Selection(
        selection=MDFE_MODALS, string="Transport Modal", default=MDFE_MODAL_DEFAULT
    )

    mdfe30_tpEmis = fields.Selection(related="mdfe_transmission")

    mdfe_transmission = fields.Selection(
        selection=MDFE_TRANSMISSIONS,
        string="Transmission",
        copy=False,
        default=lambda self: self.env.company.mdfe_transmission,
    )

    mdfe30_procEmi = fields.Selection(
        selection=MDFE_EMISSION_PROCESSES,
        string="Emission Process",
        default=MDFE_EMISSION_PROCESS_DEFAULT,
    )

    mdfe30_verProc = fields.Char(
        copy=False,
        default=lambda s: s.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_mdfe.version.name", default="Odoo Brasil OCA v14"),
    )

    mdfe30_UFIni = fields.Selection(
        compute="_compute_mdfe30_initial_final_state",
        inverse="_inverse_mdfe30_initial_final_state",
    )

    mdfe30_UFFim = fields.Selection(
        compute="_compute_mdfe30_initial_final_state",
        inverse="_inverse_mdfe30_initial_final_state",
    )

    mdfe_initial_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="Initial State",
        domain=[("country_id.code", "=", "BR")],
    )

    mdfe_final_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="Final State",
        domain=[("country_id.code", "=", "BR")],
    )

    mdfe30_cMDF = fields.Char(related="key_random_code", string="Código Numérico MDFe")

    mdfe30_cDV = fields.Char(related="key_check_digit")

    mdfe30_infMunCarrega = fields.One2many(
        compute="_compute_mdfe30_inf_carrega",
        inverse="_inverse_mdfe30_inf_carrega",
        string="Informações dos Municipios de Carregamento",
    )

    mdfe_loading_city_ids = fields.Many2many(
        comodel_name="res.city", string="Loading Cities"
    )

    mdfe30_infPercurso = fields.One2many(compute="_compute_mdfe30_inf_percurso")

    mdfe_route_state_ids = fields.Many2many(
        comodel_name="res.country.state",
        string="Route States",
        domain=[("country_id.code", "=", "BR")],
    )

    ##########################
    # MDF-e tag: ide
    # Methods
    ##########################

    @api.depends("company_id")
    def _compute_mdfe30_uf(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_cUF = record.company_id.partner_id.state_id.ibge_code

    @api.depends("mdfe_initial_state_id", "mdfe_final_state_id")
    def _compute_mdfe30_initial_final_state(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_UFIni = record.mdfe_initial_state_id.code
            record.mdfe30_UFFim = record.mdfe_final_state_id.code

    @api.depends("mdfe_loading_city_ids")
    def _compute_mdfe30_inf_carrega(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_infMunCarrega = [Command.clear()]
            record.mdfe30_infMunCarrega = [
                Command.create(
                    {
                        "mdfe30_cMunCarrega": city.ibge_code,
                        "mdfe30_xMunCarrega": city.name,
                    },
                )
                for city in record.mdfe_loading_city_ids
            ]

    def _inverse_mdfe30_inf_carrega(self):
        for record in self:
            city_ids = self.env["res.city"].search(
                [("ibge_code", "=", record.mdfe30_infMunCarrega.mdfe30_cMunCarrega)]
            )
            if city_ids:
                record.mdfe_loading_city_ids = [Command.set(city_ids.ids)]

    def _inverse_mdfe30_initial_final_state(self):
        country_id = self.env["res.country"].search([("code", "=", "BR")])
        for record in self:
            initial_state_id = self.env["res.country.state"].search(
                [
                    ("code", "=", record.mdfe30_UFIni),
                    ("country_id", "=", country_id.id),
                ],
                limit=1,
            )
            final_state_id = self.env["res.country.state"].search(
                [
                    ("code", "=", record.mdfe30_UFFim),
                    ("country_id", "=", country_id.id),
                ],
                limit=1,
            )

            if initial_state_id:
                record.mdfe_initial_state_id = initial_state_id

            if final_state_id:
                record.mdfe_final_state_id = final_state_id

    def _inverse_mdfe30_uf(self):
        country_id = self.env["res.country"].search([("code", "=", "BR")])
        for record in self:
            state_id = self.env["res.country.state"].search(
                [("code", "=", record.mdfe30_cUF), ("country_id", "=", country_id.id)],
                limit=1,
            )
            if state_id:
                record.company_id.partner_id.state_id = state_id

    @api.depends("mdfe_route_state_ids")
    def _compute_mdfe30_inf_percurso(self):
        for record in self:
            record.mdfe30_infPercurso = [Command.clear()]
            origin = record.mdfe_initial_state_id
            destination = record.mdfe_final_state_id
            record.mdfe30_infPercurso = [
                Command.create(
                    {
                        "mdfe30_UFPer": state.code,
                    },
                )
                for state in record.mdfe_route_state_ids
                if state != origin and state != destination
            ]

    ##########################
    # MDF-e tag: emit
    ##########################

    mdfe30_emit = fields.Many2one(comodel_name="res.company", related="company_id")

    ##########################
    # MDF-e tag: infModal
    ##########################

    mdfe30_versaoModal = fields.Char(default=MDFE_MODAL_VERSION_DEFAULT)

    # Campos do Modal Aéreo
    mdfe_modal_aereo_id = fields.Many2one(
        comodel_name="l10n_br_mdfe.modal.aereo", copy=False
    )

    mdfe30_nac = fields.Char(size=4, string="Nacionalidade da Aeronave")

    mdfe30_matr = fields.Char(size=6, string="Matrícula da Aeronave")

    mdfe30_nVoo = fields.Char(size=9, string="Número do Voo")

    mdfe30_dVoo = fields.Date(string="Data do Voo")

    mdfe30_cAerEmb = fields.Char(
        default=MDFE_MODAL_DEFAULT_AIRCRAFT, size=4, string="Aeródromo de Embarque"
    )

    mdfe30_cAerDes = fields.Char(
        default=MDFE_MODAL_DEFAULT_AIRCRAFT, size=4, string="Aeródromo de Destino"
    )

    # Campos do Modal Aquaviário
    mdfe_modal_aquaviario_id = fields.Many2one(
        comodel_name="l10n_br_mdfe.modal.aquaviario", copy=False
    )

    mdfe30_irin = fields.Char(size=10, string="IRIN da Embarcação")

    mdfe30_tpEmb = fields.Selection(
        selection=MDFE_MODAL_SHIP_TYPES, string="Tipo da Embarcação"
    )

    mdfe30_cEmbar = fields.Char(size=10, string="Código da Embarcação")

    mdfe30_xEmbar = fields.Char(size=60, string="Nome da Embarcação")

    mdfe30_nViag = fields.Char(string="Número da Viagem")

    mdfe30_cPrtEmb = fields.Selection(
        selection=MDFE_MODAL_HARBORS, string="Porto de Embarque"
    )

    mdfe30_cPrtDest = fields.Selection(
        selection=MDFE_MODAL_HARBORS, string="Porto de Destino"
    )

    mdfe30_prtTrans = fields.Char(size=60, string="Porto de Transbordo")

    mdfe30_tpNav = fields.Selection(selection=AQUAV_TPNAV, string="Tipo de Navegação")

    mdfe30_infTermCarreg = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.carregamento",
        inverse_name="document_id",
    )

    mdfe30_infTermDescarreg = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.descarregamento",
        inverse_name="document_id",
    )

    mdfe30_infEmbComb = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.comboio",
        inverse_name="document_id",
    )

    mdfe30_infUnidCargaVazia = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.carga.vazia",
        inverse_name="document_id",
    )

    mdfe30_infUnidTranspVazia = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.transporte.vazio",
        inverse_name="document_id",
    )

    # Campos do Modal Ferroviário
    mdfe_modal_ferroviario_id = fields.Many2one(
        comodel_name="l10n_br_mdfe.modal.ferroviario", copy=False
    )

    mdfe30_xPref = fields.Char(string="Prefixo do Trem", size=10)

    mdfe30_dhTrem = fields.Datetime(string="Data/hora de Liberação do Trem")

    mdfe30_xOri = fields.Char(string="Origem do Trem", size=3)

    mdfe30_xDest = fields.Char(string="Destino do Trem", size=3)

    mdfe30_qVag = fields.Char(string="Quantidade de Vagões")

    mdfe30_vag = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.ferroviario.vagao", inverse_name="document_id"
    )

    # Campos do Modal Rodoviário
    mdfe_modal_rodoviario_id = fields.Many2one(
        comodel_name="l10n_br_mdfe.modal.rodoviario", copy=False
    )

    mdfe30_codAgPorto = fields.Char(string="Código de Agendamento", size=16)

    mdfe30_infCIOT = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.ciot", inverse_name="document_id"
    )

    mdfe30_disp = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.vale_pedagio.dispositivo",
        inverse_name="document_id",
    )

    mdfe30_categCombVeic = fields.Selection(
        selection=VALEPED_CATEGCOMBVEIC, string="Categoria de Combinação Veicular"
    )

    mdfe30_infContratante = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.contratante",
        inverse_name="document_id",
    )

    mdfe30_RNTRC = fields.Char(
        related="company_id.partner_id.rntrc_code", string="RNTRC"
    )

    mdfe30_infPag = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.pagamento",
        inverse_name="document_id",
    )

    mdfe30_prop = fields.Many2one(
        comodel_name="res.partner", string="Proprietário do Veículo"
    )

    mdfe30_condutor = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.veiculo.condutor",
        inverse_name="document_id",
    )

    mdfe30_cInt = fields.Char(size=10, string="Código do Veículo")

    mdfe_vehicle_id = fields.Many2one(
        comodel_name="l10n_br_mdfe.vehicle",
        string="Veículo",
    )

    mdfe30_RENAVAM = fields.Char(size=11, string="RENAVAM")

    mdfe30_placa = fields.Char(string="Placa do Veículo")

    mdfe30_tara = fields.Char(string="Tara em KG")

    mdfe30_capKG = fields.Char(string="Capacidade em KG")

    mdfe30_capM3 = fields.Char(string="Capacidade em M3")

    mdfe30_tpRod = fields.Selection(selection=VEICTRACAO_TPROD, string="Tipo do Rodado")

    mdfe30_tpCar = fields.Selection(
        selection=VEICTRACAO_TPCAR, string="Tipo de Carroceria"
    )

    mdfe30_veicReboque = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.reboque",
        inverse_name="document_id",
    )

    mdfe30_lacRodo = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.lacre",
        inverse_name="document_id",
    )

    mdfe30_UF = fields.Selection(selection=TUF, compute="_compute_mdfe30_rodo_uf")

    rodo_vehicle_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="UF do Veículo",
        domain=[("country_id.code", "=", "BR")],
    )

    ##########################
    # MDF-e tag: infModal
    # Methods
    ##########################

    @api.depends("rodo_vehicle_state_id")
    def _compute_mdfe30_rodo_uf(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_UF = record.rodo_vehicle_state_id.code

    @api.onchange("mdfe_vehicle_id")
    def _onchange_mdfe_vehicle_id(self):
        if self.mdfe_vehicle_id:
            vehicle = self.mdfe_vehicle_id
            self.mdfe30_cInt = vehicle.mdfe30_cInt
            self.mdfe30_placa = vehicle.mdfe30_placa
            self.mdfe30_RENAVAM = vehicle.mdfe30_RENAVAM
            self.mdfe30_tara = vehicle.mdfe30_tara
            self.mdfe30_capKG = vehicle.mdfe30_capKG
            self.mdfe30_capM3 = vehicle.mdfe30_capM3
            self.mdfe30_tpRod = vehicle.mdfe30_tpRod
            self.mdfe30_tpCar = vehicle.mdfe30_tpCar
            self.rodo_vehicle_state_id = vehicle.rodo_vehicle_state_id

    def _export_fields_mdfe_30_infmodal(self, xsd_fields, class_obj, export_dict):
        if self.mdfe_modal == "1":
            export_dict["any_element"] = self._export_mdfe_modal_rodoviario()
        elif self.mdfe_modal == "2":
            export_dict["any_element"] = self._export_mdfe_modal_aereo()
        elif self.mdfe_modal == "3":
            export_dict["any_element"] = self._export_mdfe_modal_aquaviario()
        elif self.mdfe_modal == "4":
            export_dict["any_element"] = self._export_mdfe_modal_ferroviario()

    def _export_mdfe_modal_aereo(self):
        if not self.mdfe_modal_aereo_id:
            self.mdfe_modal_aereo_id = self.mdfe_modal_aereo_id.create(
                {"document_id": self.id}
            )

        return self.mdfe_modal_aereo_id._build_binding("mdfe", "30")

    def _export_mdfe_modal_ferroviario(self):
        if not self.mdfe_modal_ferroviario_id:
            self.mdfe_modal_ferroviario_id = self.mdfe_modal_ferroviario_id.create(
                {"document_id": self.id}
            )

        return self.mdfe_modal_ferroviario_id._build_binding("mdfe", "30")

    def _export_mdfe_modal_aquaviario(self):
        if not self.mdfe_modal_aquaviario_id:
            self.mdfe_modal_aquaviario_id = self.mdfe_modal_aquaviario_id.create(
                {"document_id": self.id}
            )

        return self.mdfe_modal_aquaviario_id._build_binding("mdfe", "30")

    def _export_mdfe_modal_rodoviario(self):
        if not self.mdfe_modal_rodoviario_id:
            self.mdfe_modal_rodoviario_id = self.mdfe_modal_rodoviario_id.create(
                {"document_id": self.id}
            )

        return self.mdfe_modal_rodoviario_id._build_binding("mdfe", "30")

    ##########################
    # MDF-e tag: seg
    ##########################

    mdfe30_seg = fields.One2many(
        comodel_name="l10n_br_mdfe.seguro.carga",
        inverse_name="document_id",
        string="Seguros da Carga",
    )

    ##########################
    # MDF-e tag: prodPred
    ##########################

    mdfe30_prodPred = fields.Many2one(comodel_name="product.product")

    ##########################
    # MDF-e tag: lacres
    ##########################

    mdfe30_lacres = fields.One2many(
        comodel_name="l10n_br_mdfe.transporte.lacre",
        inverse_name="document_id",
    )

    ##########################
    # MDF-e tag: infDoc
    ##########################

    mdfe30_infMunDescarga = fields.One2many(
        comodel_name="l10n_br_mdfe.municipio.descarga", inverse_name="document_id"
    )

    mdfe_document_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.document",
        relation="mdfe_m2m_document_rel",
        column1="mdfe_document_id",
        column2="related_document_id",
        string="Related Documents",
    )

    mdfe_nfe_ids = fields.Many2many(
        related="mdfe_document_ids",
        string="Related Documents (legacy)",
    )

    mdfe_cte_ids = fields.Many2many(
        related="mdfe_document_ids",
        string="Related Documents (legacy)",
    )

    mdfe_mdfe_ids = fields.Many2many(
        related="mdfe_document_ids",
        string="Related Documents (legacy)",
    )

    ##########################
    # MDF-e tag: infRespTec
    ##########################

    mdfe30_infRespTec = fields.Many2one(
        comodel_name="res.partner",
        related="company_id.technical_support_id",
        string="Responsável Técnico MDFe",
    )

    ##########################
    # NF-e tag: infAdic
    ##########################

    mdfe30_infAdFisco = fields.Char(
        compute="_compute_mdfe30_additional_data",
        string="Informações Adicionais Fiscais MDFe",
    )

    mdfe30_infCpl = fields.Char(
        compute="_compute_mdfe30_additional_data",
        string="Informações Complementares MDFE",
    )

    ##########################
    # MDF-e tag: infAdic
    # Methods
    ##########################

    @api.depends("fiscal_additional_data")
    def _compute_mdfe30_additional_data(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_infCpl = False
            record.mdfe30_infAdFisco = False

            if record.fiscal_additional_data:
                record.mdfe30_infAdFisco = (
                    normalize("NFKD", record.fiscal_additional_data)
                    .encode("ASCII", "ignore")
                    .decode("ASCII")
                    .replace("\n", "")
                    .replace("\r", "")
                )
            if record.customer_additional_data:
                record.mdfe30_infCpl = (
                    normalize("NFKD", record.customer_additional_data)
                    .encode("ASCII", "ignore")
                    .decode("ASCII")
                    .replace("\n", "")
                    .replace("\r", "")
                )

    ##########################
    # MDF-e tag: autXML
    ##########################

    def _default_mdfe30_autxml(self):
        company = self.env.company
        authorized_partners = []
        if company.accountant_id:
            authorized_partners.append(company.accountant_id.id)
        if company.technical_support_id:
            authorized_partners.append(company.technical_support_id.id)
        return authorized_partners

    mdfe30_autXML = fields.One2many(default=_default_mdfe30_autxml)

    ##########################
    # NF-e tag: tot
    ##########################

    mdfe30_qCTe = fields.Integer(
        compute="_compute_mdfe30_tot", store=True, readonly=False
    )

    mdfe30_qNFe = fields.Integer(
        compute="_compute_mdfe30_tot", store=True, readonly=False
    )

    mdfe30_qMDFe = fields.Integer(
        compute="_compute_mdfe30_tot", store=True, readonly=False
    )

    mdfe30_qCarga = fields.Float(
        compute="_compute_mdfe30_tot", store=True, readonly=False
    )

    mdfe30_vCarga = fields.Float(
        compute="_compute_mdfe30_tot", store=True, readonly=False
    )

    mdfe30_cUnid = fields.Selection(default="01")

    partner_city_id = fields.Many2one(
        comodel_name="res.city",
        string="Partner City",
        compute="_compute_partner_city_id",
        store=True,
    )

    @api.depends("partner_id.city_id")
    def _compute_partner_city_id(self):
        for record in self:
            record.partner_city_id = record.partner_id.city_id

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if any(f in vals for f in ["mdfe_document_ids"]):
            rec._sync_mdfe_documents()
        return rec

    def write(self, vals):
        res = super().write(vals)
        if "mdfe_document_ids" in vals:
            self._sync_mdfe_documents()
        return res

    def _sync_mdfe_documents(self):
        doc_type_map = {"55": "nfe", "59": "cte", "58": "mdfe"}
        for record in self.filtered(filtered_processador_edoc_mdfe):
            all_cities = {}
            for doc in record.mdfe_document_ids:
                doc_type = doc_type_map.get(doc.document_type, "nfe")
                partner = doc.partner_id
                city = partner.city_id if partner else False
                city_key = (city.id, doc_type) if city else (0, doc_type)
                if city_key not in all_cities:
                    all_cities[city_key] = {"city": city, "type": doc_type, "docs": []}
                all_cities[city_key]["docs"].append(doc)

            unlink_ids = record.mdfe30_infMunDescarga.ids
            doc_rel_model = self.env["l10n_br_fiscal.document.related"]
            for (city_id, doc_type), info in all_cities.items():
                existing = record.mdfe30_infMunDescarga.filtered(
                    lambda r, c=city_id, t=doc_type: (
                        r.city_id.id == c if c else not r.city_id
                    )
                    and r.document_type == t
                )
                if existing:
                    munic = existing[0]
                    if munic.id in unlink_ids:
                        unlink_ids.remove(munic.id)
                else:
                    munic = record.mdfe30_infMunDescarga.create(
                        {
                            "document_id": record.id,
                            "city_id": city_id or False,
                            "document_type": doc_type,
                        }
                    )

                related_ids = []
                for doc in info["docs"]:
                    related = doc_rel_model.search(
                        [
                            ("document_related_id", "=", doc.id),
                        ],
                        limit=1,
                    )
                    if not related:
                        related = doc_rel_model.create(
                            {
                                "document_related_id": doc.id,
                                "document_type_id": doc.document_type_id.id,
                                "document_key": doc.document_key,
                                "document_serie": doc.document_serie,
                                "document_number": doc.document_number,
                                "document_total_amount": doc.fiscal_amount_total,
                                "document_total_weight": doc.total_weight,
                            }
                        )
                    related_ids.append(related.id)
                munic.write({f"{doc_type}_ids": [(6, 0, related_ids)]})

            if unlink_ids:
                record.mdfe30_infMunDescarga.browse(unlink_ids).unlink()

    ##########################
    # MDF-e tag: tot
    # Methods
    ##########################

    @api.depends(
        "mdfe30_infMunDescarga.cte_ids",
        "mdfe30_infMunDescarga.nfe_ids",
        "mdfe30_infMunDescarga.mdfe_ids",
    )
    def _compute_mdfe30_tot(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_qCarga = 0
            record.mdfe30_vCarga = 0

            cte_ids = record.mdfe30_infMunDescarga.mapped("cte_ids")
            nfe_ids = record.mdfe30_infMunDescarga.mapped("nfe_ids")
            mdfe_ids = record.mdfe30_infMunDescarga.mapped("mdfe_ids")

            record.mdfe30_qCTe = cte_ids and len(cte_ids) or False
            record.mdfe30_qNFe = nfe_ids and len(nfe_ids) or False
            record.mdfe30_qMDFe = mdfe_ids and len(mdfe_ids) or False

            all_documents = cte_ids + nfe_ids + mdfe_ids
            record.mdfe30_qCarga = sum(all_documents.mapped("document_total_weight"))
            record.mdfe30_vCarga = sum(all_documents.mapped("document_total_amount"))

    ##########################
    # NF-e tag: infMDFeSupl
    ##########################

    mdfe30_infMDFeSupl = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.supplement",
    )

    ##########################
    # Other fields
    ##########################

    closure_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.event",
        string="Closure Event",
        copy=False,
    )

    closure_state_id = fields.Many2one(comodel_name="res.country.state")

    closure_city_id = fields.Many2one(comodel_name="res.city")

    ################################
    # Framework Spec model's methods
    ################################

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        doc_type_id = res.get("document_type_id") or self._context.get(
            "default_document_type_id"
        )
        if doc_type_id:
            doc_type = self.env["l10n_br_fiscal.document.type"].browse(doc_type_id)
            if doc_type.code == MODELO_FISCAL_MDFE:
                company = self.env.company
                if not res.get("company_id"):
                    res["company_id"] = company.id
                if not res.get("user_id"):
                    res["user_id"] = self.env.user.id
                if company.partner_id.state_id and not res.get("mdfe_initial_state_id"):
                    res["mdfe_initial_state_id"] = company.partner_id.state_id.id
                if not res.get("mdfe_vehicle_id"):
                    first_vehicle = self.env["l10n_br_mdfe.vehicle"].search(
                        [
                            ("partner_id", "child_of", company.partner_id.id),
                            ("active", "=", True),
                        ],
                        limit=1,
                    )
                    if first_vehicle:
                        res["mdfe_vehicle_id"] = first_vehicle.id
                if not res.get("document_serie_id"):
                    serie = doc_type.get_document_serie(company, None)
                    if serie:
                        res["document_serie_id"] = serie.id
                if not res.get("partner_id"):
                    if company.partner_id:
                        res["partner_id"] = company.partner_id.id
                if "mdfe_loading_city_ids" in fields and not res.get(
                    "mdfe_loading_city_ids"
                ):
                    if company.city_id:
                        res["mdfe_loading_city_ids"] = [
                            Command.set([company.city_id.id])
                        ]
        return res

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        if field_name == "mdfe30_prodPred":
            if self.mdfe30_prodPred.mdfe30_infLotacao:
                self.mdfe30_prodPred.mdfe30_infLotacao.unlink()

            cte_ids = self.mdfe30_infMunDescarga.mapped("cte_ids")
            nfe_ids = self.mdfe30_infMunDescarga.mapped("nfe_ids")
            mdfe_ids = self.mdfe30_infMunDescarga.mapped("mdfe_ids")

            total_dfe = len(cte_ids) + len(nfe_ids) + len(mdfe_ids)
            if total_dfe != 1:
                self.mdfe30_prodPred.mdfe30_NCM = False

            elif total_dfe == 1 and not self.mdfe30_infPag:
                raise UserError(
                    _(
                        "Payment information (infPag) "
                        "must be provided when the MDF-e contains "
                        "only one DF-e (full load)."
                    )
                )

            cep_carrega, cep_descarrega = None, None

            if len(cte_ids) == 1 or len(nfe_ids) == 1 or len(mdfe_ids) == 1:
                cte_doc = cte_ids and cte_ids[0].document_related_id
                nfe_doc = nfe_ids and nfe_ids[0].document_related_id
                mdfe_doc = mdfe_ids and mdfe_ids[0].document_related_id

                if cte_doc:
                    cep_carrega = (
                        cte_doc.cte40_rem.zip if hasattr(cte_doc, "cte40_rem") else None
                    )
                    cep_descarrega = (
                        cte_doc.cte40_dest.zip
                        if hasattr(cte_doc, "cte40_dest")
                        else None
                    )

                elif nfe_doc:
                    cep_carrega = (
                        nfe_doc.nfe40_enderEmit.zip
                        if hasattr(nfe_doc, "nfe40_enderEmit")
                        else None
                    )
                    cep_descarrega = (
                        nfe_doc.nfe40_enderDest.zip
                        if hasattr(nfe_doc, "nfe40_enderDest")
                        else None
                    )
                elif mdfe_doc:
                    cep_carrega = mdfe_doc.mdfe30_emit.zip
                    cep_descarrega = mdfe_doc.mdfe30_emit.zip

                # Caso não tenha documentos relacionados ou campos específicos
                if not cep_carrega or not cep_descarrega:
                    cep_carrega = self.mdfe30_emit.zip
                    cep_descarrega = self.mdfe30_emit.zip

            local_carrega = (
                self.env["l10n_br_mdfe.product.lotacao.local"]
                .sudo()
                .create(
                    {
                        "local_type": "CEP",
                        "mdfe30_CEP": punctuation_rm(cep_carrega),
                    }
                )
            )

            local_descarrega = (
                self.env["l10n_br_mdfe.product.lotacao.local"]
                .sudo()
                .create(
                    {
                        "local_type": "CEP",
                        "mdfe30_CEP": punctuation_rm(cep_descarrega),
                    }
                )
            )

            if cep_carrega and cep_descarrega:
                self.mdfe30_prodPred.mdfe30_infLotacao = (
                    self.env["l10n_br_mdfe.product.lotacao"]
                    .sudo()
                    .create(
                        {
                            "product_id": self.mdfe30_prodPred.id,
                            "mdfe30_infLocalCarrega": local_carrega.id,
                            "mdfe30_infLocalDescarrega": local_descarrega.id,
                        }
                    )
                )

        elif field_name == "mdfe30_infModal":
            return self._build_binding(
                class_name=class_obj._fields[field_name].comodel_name
            )

        return super()._export_many2one(field_name, xsd_required, class_obj)

    def _prepare_import_dict(
        self, values, model=None, parent_dict=None, defaults_model=None
    ):
        res = super()._prepare_import_dict(values, model, parent_dict, defaults_model)
        res["imported_document"] = True
        if "mdfe30_mod" in values:
            res["document_type_id"] = (
                self.env["l10n_br_fiscal.document.type"]
                .search([("code", "=", values["mdfe30_mod"])], limit=1)
                .id
            )
        return res

    def _get_mdfe_modal_to_build(self, module):
        modal_by_binding_module = {
            self.mdfe_modal_rodoviario_id._binding_module: (
                self.mdfe_modal_rodoviario_id
            ),
            self.mdfe_modal_aereo_id._binding_module: self.mdfe_modal_aereo_id,
            self.mdfe_modal_aquaviario_id._binding_module: (
                self.mdfe_modal_aquaviario_id
            ),
            self.mdfe_modal_ferroviario_id._binding_module: (
                self.mdfe_modal_ferroviario_id
            ),
        }
        return modal_by_binding_module.get(module, False)

    def _build_many2one(self, comodel, vals, new_value, key, value, path):
        if key == "mdfe30_emit" and self.env.context.get("edoc_type") == "in":
            enderEmit_value = self.env["res.partner"].build_attrs(
                value.enderEmit, path=path
            )
            new_value.update(enderEmit_value)
            company_cnpj = self.env.user.company_id.cnpj_cpf.translate(
                str.maketrans("", "", string.punctuation)
            )
            emit_cnpj = new_value.get("mdfe30_CNPJ", False)
            if emit_cnpj:
                emit_cnpj = new_value.get("mdfe30_CNPJ").translate(
                    str.maketrans("", "", string.punctuation)
                )
                if company_cnpj != emit_cnpj:
                    vals["issuer"] = "partner"
                new_value["is_company"] = True
                new_value["cnpj_cpf"] = emit_cnpj
            return super()._build_many2one(
                self.env["res.partner"], vals, new_value, "partner_id", value, path
            )

        else:
            return super()._build_many2one(comodel, vals, new_value, key, value, path)

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        if rec_dict.get("mdfe30_Id"):
            domain = [("mdfe30_Id", "=", rec_dict.get("mdfe30_Id"))]
            match = self.search(domain, limit=1)
            if match:
                return match.id
        return False

    def import_binding_mdfe(self, binding, edoc_type="in", dry_run=False):
        if hasattr(binding, "MDFe"):
            binding = binding.MDFe
        document = (
            self.env["mdfe.30.tmdfe_infmdfe"]
            .with_context(tracking_disable=True, edoc_type=edoc_type)
            .build_from_binding("mdfe", "30", binding.infMDFe, dry_run=dry_run)
        )

        if edoc_type == "in" and document.company_id.vat != cnpj_cpf.formata(
            binding.infMDFe.emit.CNPJ
        ):
            document.fiscal_operation_type = "in"
            document.issuer = "partner"
        return document

    ################################
    # Business Model Methods
    ################################

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.with_context(lang="pt_BR").filtered(
            filtered_processador_edoc_mdfe
        ):
            inf_mdfe = record._build_binding("mdfe", "30")

            inf_mdfe_supl = None
            if record.mdfe30_infMDFeSupl:
                inf_mdfe_supl = record.mdfe30_infMDFeSupl._build_binding("mdfe", "30")

            mdfe = Mdfe(infMDFe=inf_mdfe, infMDFeSupl=inf_mdfe_supl, signature=None)
            edocs.append(mdfe)
        return edocs

    def _edoc_processor(self):
        if self.document_type != MODELO_FISCAL_MDFE:
            return super()._edoc_processor()

        certificado = self.company_id._get_br_ecertificate()

        session = Session()
        session.verify = False

        params = {
            "transmissao": TransmissaoMDFE(certificado, session),
            "uf": self.company_id.state_id.ibge_code,
            "versao": self.mdfe_version,
            "ambiente": self.mdfe_environment,
        }
        return edoc_mdfe(**params)

    def _generate_key(self):
        if self.document_type_id.code not in [MODELO_FISCAL_MDFE]:
            return super()._generate_key()

        for record in self:
            cnpj_cpf = record.company_id.cnpj_cpf or record.company_id.vat
            if not cnpj_cpf:
                raise ValidationError(
                    _(
                        "To Generate EDoc Key, you need to fill the CNPJ/CPF "
                        "field on company %s."
                    )
                    % record.company_id.display_name
                )
            if not record.company_id.state_id:
                raise ValidationError(
                    _(
                        "To Generate EDoc Key, you need to fill the State "
                        "on company %s."
                    )
                    % record.company_id.display_name
                )
            if not record.document_type_id:
                raise ValidationError(_("Document Type is not defined."))
            if not record.document_number:
                if record.document_serie_id:
                    record.document_number = record.document_serie_id.next_seq_number()
                if not record.document_number:
                    raise ValidationError(
                        _(
                            "To Generate EDoc Key, you need to fill the "
                            "Document Number."
                        )
                    )
            if not record.document_serie:
                if record.document_serie_id:
                    record.document_serie = record.document_serie_id.code
                if not record.document_serie:
                    raise ValidationError(
                        _(
                            "To Generate EDoc Key, you need to fill the "
                            "Document Serie."
                        )
                    )

            date = fields.Datetime.context_timestamp(record, record.document_date)

            if filtered_processador_edoc_mdfe(record):
                if not record.mdfe_transmission:
                    raise ValidationError(
                        _(
                            "To Generate EDoc Key, you need to fill the "
                            "MDFe Transmission field."
                        )
                    )
                forma_emissao = int(punctuation_rm(str(record.mdfe_transmission)))
                fields_to_validate = {
                    "CNPJ/CPF": cnpj_cpf,
                    "UF": record.company_id.state_id.ibge_code,
                    "Document Type": record.document_type_id.code,
                    "Document Number": record.document_number,
                    "Document Serie": record.document_serie,
                    "MDFe Transmission": record.mdfe_transmission,
                }
                cleaned_fields = {}
                for label, value in fields_to_validate.items():
                    cleaned = punctuation_rm(str(value or ""))
                    if cleaned and not cleaned.isdigit():
                        raise ValidationError(
                            _(
                                "The field %(label)s must contain only numbers. "
                                "Found: '%(value)s'"
                            )
                            % {"label": label, "value": value}
                        )
                    cleaned_fields[label] = cleaned
                chave_kw = {
                    "ano_mes": date.strftime("%y%m").zfill(4),
                    "cnpj_cpf_emitente": cleaned_fields["CNPJ/CPF"],
                    "codigo_uf": cleaned_fields["UF"],
                    "forma_emissao": forma_emissao,
                    "modelo_documento": cleaned_fields["Document Type"],
                    "numero_documento": cleaned_fields["Document Number"],
                    "numero_serie": cleaned_fields["Document Serie"],
                }
            else:
                chave_kw = {
                    "ano_mes": date.strftime("%y%m").zfill(4),
                    "cnpj_cpf_emitente": punctuation_rm(str(cnpj_cpf or "")),
                    "codigo_uf": record.company_id.state_id.ibge_code,
                    "forma_emissao": 1,
                    "modelo_documento": record.document_type_id.code,
                    "numero_documento": record.document_number,
                    "numero_serie": record.document_serie,
                }

            chave_edoc = ChaveEdoc(validar=False, **chave_kw)
            record.key_random_code = chave_edoc.codigo_aleatorio
            record.key_check_digit = chave_edoc.digito_verificador
            record.document_key = chave_edoc.chave

    def _document_number(self):
        if (
            self.issuer == DOCUMENT_ISSUER_COMPANY
            and not self.document_serie_id
            and self.document_type_id
        ):
            serie = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )
            if serie:
                self.document_serie_id = serie
        return super()._document_number()

    def _document_check(self):
        result = super()._document_check()
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record._check_mdfe_required_fields()
        return result

    def _check_mdfe_required_fields(self):
        self.ensure_one()

        missing_fields = []

        def check(value, label):
            if not value:
                missing_fields.append(label)

        company = self.company_id
        certificate = (
            company.sudo().certificate_nfe_id or company.sudo().certificate_ecnpj_id
        )

        check(company, _("Company"))
        check(company.vat, _("Company CNPJ/CPF"))
        check(company.state_id, _("Company State"))
        check(certificate, _("Digital Certificate"))
        if certificate:
            check(certificate.file, _("Digital Certificate File"))
            check(certificate.password, _("Digital Certificate Password"))

        check(self.document_type_id, _("Document Type"))
        check(self.document_serie, _("Document Serie"))
        check(self.document_number, _("Document Number"))
        check(self.document_date, _("Document Date"))
        check(self.mdfe_version, _("MDF-e Version"))
        check(self.mdfe_environment, _("MDF-e Environment"))
        check(self.mdfe_emit_type, _("MDF-e Emit Type"))
        # mdfe_transp_type is only required when a third-party owner is set.
        # It is validated together with mdfe30_prop in _check_mdfe_road_required_fields.
        check(self.mdfe_modal, _("MDF-e Modal"))
        check(self.mdfe_transmission, _("MDF-e Transmission"))
        check(self.mdfe_initial_state_id, _("MDF-e Initial State"))
        check(self.mdfe_final_state_id, _("MDF-e Final State"))
        check(self.mdfe_loading_city_ids, _("MDF-e Loading City"))
        check(self.mdfe30_infMunDescarga, _("MDF-e Unloading City"))

        for descarga in self.mdfe30_infMunDescarga:
            label = descarga.city_id.display_name or _("Unloading City")
            check(descarga.city_id, _("MDF-e Unloading City"))
            if descarga.document_type == "nfe":
                check(
                    descarga.nfe_ids, _("NF-e documents for unloading city %s") % label
                )
            elif descarga.document_type == "cte":
                check(
                    descarga.cte_ids, _("CT-e documents for unloading city %s") % label
                )
            elif descarga.document_type == "mdfe":
                check(
                    descarga.mdfe_ids,
                    _("MDF-e transport documents for unloading city %s") % label,
                )

            for document in descarga.nfe_ids + descarga.cte_ids + descarga.mdfe_ids:
                check(document.document_key, _("Document Key for %s") % label)

        if self.mdfe_modal == "1":
            self._check_mdfe_road_required_fields(missing_fields)

        if missing_fields:
            raise UserError(
                _("Fill in the required MDF-e fields before sending:\n- %s")
                % "\n- ".join(missing_fields)
            )

    def _check_mdfe_road_required_fields(self, missing_fields):
        def check(value, label):
            if not value:
                missing_fields.append(label)

        check(self.mdfe30_placa, _("Vehicle Plate"))
        check(self.mdfe30_tara, _("Vehicle Tare in KG"))
        check(self.mdfe30_tpRod, _("Vehicle Wheel Type"))
        check(self.mdfe30_tpCar, _("Vehicle Body Type"))
        check(self.mdfe30_condutor, _("Vehicle Driver"))

        if self.mdfe30_prop:
            if self.mdfe30_prop == self.company_id.partner_id:
                missing_fields.append(
                    _(
                        "Vehicle Owner must be different from the MDF-e issuer. "
                        "If the vehicle belongs to your company, clear the "
                        "Transport Type field instead of filling an owner."
                    )
                )
            elif not self.mdfe_transp_type:
                missing_fields.append(
                    _(
                        "Transport Type must be informed when a third-party "
                        "vehicle owner is specified."
                    )
                )
        elif self.mdfe_transp_type:
            missing_fields.append(
                _(
                    "Vehicle Owner is required when Transport Type is informed. "
                    "If the vehicle belongs to your company, clear the "
                    "Transport Type field."
                )
            )

        if self.mdfe30_prop:
            owner_rntrc = self.mdfe30_prop.rntrc_code
            if owner_rntrc and (not owner_rntrc.isdigit() or len(owner_rntrc) != 8):
                missing_fields.append(_("Owner RNTRC must contain exactly 8 digits."))

        for condutor in self.mdfe30_condutor:
            check(condutor.mdfe30_xNome, _("Driver Name"))
            check(condutor.mdfe30_CPF, _("Driver CPF"))

    def _document_export(self, pretty_print=True):
        result = super()._document_export()
        for record in self.filtered(filtered_processador_edoc_mdfe):
            edoc = record.serialize()[0]
            processador = record._edoc_processor()
            xml_file = processador.render_edoc_xsdata(edoc, pretty_print=pretty_print)[
                0
            ]
            xml_file = edoc.to_xml()
            # Delete previous authorization events in draft
            if (
                record.authorization_event_id
                and record.authorization_event_id.state == "draft"
            ):
                record.sudo().authorization_event_id.unlink()

            event_id = self.event_ids.create_event_save_xml(
                company_id=self.company_id,
                environment=(
                    EVENT_ENV_PROD if self.mdfe_environment == "1" else EVENT_ENV_HML
                ),
                event_type="0",
                xml_file=xml_file,
                document_id=self,
            )
            record.authorization_event_id = event_id
            signed_xml = edoc.sign_xml(
                xml_file,
                self.company_id.certificate.file,
                self.company_id.certificate.password,
                edoc.infMDFe.Id,
            )
            self._validate_xml(signed_xml)

        return result

    def _validate_xml(self, xml_file):
        self.ensure_one()

        if self.document_type != MODELO_FISCAL_MDFE:
            return super()._validate_xml(xml_file)

        erros = Mdfe.schema_validation(xml_file)
        erros = "\n".join(erros)
        self.write({"xml_error_message": erros or False})
        if erros:
            raise UserError(_("Invalid MDF-e XML:\n%s") % erros)

    def update_status_mdfe(self, process):
        self.ensure_one()

        if hasattr(process, "protocolo"):
            infProt = process.protocolo.infProt
        else:
            infProt = process.resposta.protMDFe.infProt

        if infProt.cStat in AUTORIZADO:
            state = SITUACAO_EDOC_AUTORIZADA
            self._mdfe_response_add_proc(process)
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
        result = super()._eletronic_document_send()
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record._document_qrcode()
            record._document_export()
            if record.xml_error_message:
                raise UserError(_("Invalid MDF-e XML:\n%s") % record.xml_error_message)
            processador = record._edoc_processor()
            for edoc in record.serialize():
                process = None
                for p in processador.processar_documento(edoc):
                    process = p
                if process.webservice == "mdfeRecepcao":
                    record.authorization_event_id._save_event_file(
                        record.send_file_id.raw.decode("utf-8"), "xml"
                    )
                if process.resposta.cStat in LOTE_PROCESSADO + ["100"]:
                    record.update_status_mdfe(process)
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
        return result

    def _mdfe_cancel(self):
        self.ensure_one()
        processador = self._edoc_processor()

        if not self.authorization_protocol:
            raise UserError(_("Authorization Protocol Not Found!"))

        processo = processador.cancela_documento(
            chave=self.document_key,
            protocolo_autorizacao=self.authorization_protocol,
            justificativa=self.cancel_reason.replace("\n", "\\n"),
        )

        self.cancel_event_id = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=(
                EVENT_ENV_PROD if self.mdfe_environment == "1" else EVENT_ENV_HML
            ),
            event_type="2",
            xml_file=etree.tostring(
                processo.envio_xml, pretty_print=True, encoding="utf-8"
            ).decode("utf-8"),
            document_id=self,
        )

        infEvento = processo.resposta.infEvento
        if infEvento.cStat not in CANCELADO:
            mensagem = "Erro no cancelamento"
            mensagem += "\nCódigo: " + infEvento.cStat
            mensagem += "\nMotivo: " + infEvento.xMotivo
            raise UserError(mensagem)

        if infEvento.cStat in CANCELADO_FORA_PRAZO:
            self.state_fiscal = SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO
        elif infEvento.cStat in CANCELADO_DENTRO_PRAZO:
            self.state_fiscal = SITUACAO_FISCAL_CANCELADO

            self.state_edoc = SITUACAO_EDOC_CANCELADA
            self.cancel_event_id.set_done(
                status_code=infEvento.cStat,
                response=infEvento.xMotivo,
                protocol_date=fields.Datetime.to_string(
                    datetime.fromisoformat(infEvento.dhRegEvento)
                ),
                protocol_number=infEvento.nProt,
                file_response_xml=processo.retorno.content.decode("utf-8"),
            )

    def _document_closure(self):
        self.ensure_one()
        processador = self._edoc_processor()

        if not self.authorization_protocol:
            raise UserError(_("Authorization Protocol Not Found!"))

        processo = processador.encerra_documento(
            chave=self.document_key,
            protocolo_autorizacao=self.authorization_protocol,
            estado=self.closure_state_id.ibge_code,
            municipio=self.closure_city_id.ibge_code,
        )

        self.closure_event_id = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=(
                EVENT_ENV_PROD if self.mdfe_environment == "1" else EVENT_ENV_HML
            ),
            event_type="15",
            xml_file=etree.tostring(
                processo.envio_xml, pretty_print=True, encoding="utf-8"
            ).decode("utf-8"),
            document_id=self,
        )

        infEvento = processo.resposta.infEvento
        if infEvento.cStat not in ENCERRADO:
            mensagem = "Erro no encerramento"
            mensagem += "\nCódigo: " + infEvento.cStat
            mensagem += "\nMotivo: " + infEvento.xMotivo
            raise UserError(mensagem)

        self.state_edoc = SITUACAO_EDOC_ENCERRADA
        self.closure_event_id.set_done(
            status_code=infEvento.cStat,
            response=infEvento.xMotivo,
            protocol_date=fields.Datetime.to_string(
                datetime.fromisoformat(infEvento.dhRegEvento)
            ),
            protocol_number=infEvento.nProt,
            file_response_xml=processo.retorno.content.decode("utf-8"),
        )

    def _document_cancel(self, justificative):
        if self.document_type_id.code in [MODELO_FISCAL_MDFE]:
            if not justificative or len(justificative) < 15:
                raise ValidationError(
                    _(
                        "Please enter a justification that is at least 15 characters "
                        "long."
                    )
                )
        result = super()._document_cancel(justificative)
        online_event = self.filtered(filtered_processador_edoc_mdfe)
        if online_event:
            online_event._mdfe_cancel()
        return result

    def action_document_closure(self):
        self.ensure_one()

        if self.document_type_id.code not in [MODELO_FISCAL_MDFE]:
            raise ValidationError(
                _(
                    "The selected document type is not valid for this operation. "
                    "Please verify your input and try again."
                )
            )
        if self.state_edoc != SITUACAO_EDOC_AUTORIZADA:
            raise UserError(_("You cannot close the document if it's not authorized."))

        return self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_br_mdfe.document_closure_wizard_action"
        )

    def _document_qrcode(self):
        res = super()._document_qrcode()
        for record in self.filtered(filtered_processador_edoc_mdfe):
            if record.mdfe30_infMDFeSupl:
                record.mdfe30_infMDFeSupl.qrcode = record.get_mdfe_qrcode()
            else:
                record.mdfe30_infMDFeSupl = self.env[
                    "l10n_br_fiscal.document.supplement"
                ].create(
                    {
                        "qrcode": record.get_mdfe_qrcode(),
                    }
                )
        return res

    def get_mdfe_qrcode(self):
        if self.document_type != MODELO_FISCAL_MDFE:
            return

        processador = self._edoc_processor()
        return processador.monta_qrcode(self.document_key)

    def _mdfe_response_add_proc(self, ws_response_process):
        """
        Inject the final NF-e, tag `mdfeProc`, into the response.
        """
        xml_soap = ws_response_process.retorno.content
        tree_soap = etree.fromstring(xml_soap)
        prot_element = tree_soap.xpath(
            "//mdfe:protMDFe", namespaces=MDFE_XML_NAMESPACE
        )[0]
        proc_xml = self._mdfe_create_proc(prot_element)
        if proc_xml:
            # it is not always possible to create mdfeProc.
            parser = XmlParser()
            proc = parser.from_string(proc_xml.decode(), MdfeProc)
            ws_response_process.processo = proc
            ws_response_process.processo_xml = proc_xml

    def _mdfe_create_proc(self, prot_element):
        """
        Create the `mdfeProc` XML by combining the MDF-e and the authorization protocol.

        This method decodes the saved `enviMDFe` message, extracts the MDFe> tag,
        and combines it with the provided authorization protocol element to create
        the `mdfeProc` XML, which represents the finalized MDF-e document.

        Args:
            prot_element: The XML element containing the authorization protocol.

        Returns:
            The assembled `mdfeProc` XML, or None if the `send_file_id` data is not
            found.

        Note:
            Useful for recreating the final MDF-e XML, as SEFAZ does not provide the
            complete XML upon consultation, only the authorization protocol.
        """
        self.ensure_one()

        if not self.send_file_id.datas:
            _logger.info(
                "MDF-e data not found when trying to assemble the "
                "xml with the authorization protocol (mdfeProc)"
            )
            return None

        processor = self._edoc_processor()

        # Extract the <MDFe> tag from the `enviMDFe` message, which represents the MDF-e
        xml_send = base64.b64decode(self.send_file_id.datas)
        tree_send = etree.fromstring(xml_send)
        doc_element = tree_send.xpath("//mdfe:MDFe", namespaces=MDFE_XML_NAMESPACE)[0]

        # Assemble the `mdfeProc` using the erpbrasil.edoc library.
        proc_xml = processor.monta_mdfe_proc(doc=doc_element, prot=prot_element)

        return proc_xml

    def make_pdf(self):
        if not self.filtered(filtered_processador_edoc_mdfe):
            return super().make_pdf()

        attachment_data = {
            "name": self.document_key + ".pdf",
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/pdf",
            "type": "binary",
        }
        report = self.env.ref("l10n_br_mdfe.main_template_damdfe")
        pdf_data = report._render_qweb_pdf("main_template_damdfe", self.ids)
        attachment_data["datas"] = base64.b64encode(pdf_data[0])
        file_pdf = self.file_report_id
        self.file_report_id = False
        file_pdf.unlink()

        self.file_report_id = self.env["ir.attachment"].create(attachment_data)


class MDFeProductLotacao(spec_models.SpecModel):
    _name = "l10n_br_mdfe.inflotacao"
    _inherit = "mdfe.30.inflotacao"
    _description = "Informações De Lotação MDFe"

    product_id = fields.Many2one(comodel_name="product.product")

    mdfe30_infLocalCarrega = fields.Many2one(
        comodel_name="l10n_br_mdfe.inflotacao.local",
        required=True,
    )

    mdfe30_infLocalDescarrega = fields.Many2one(
        comodel_name="l10n_br_mdfe.inflotacao.local",
        required=True,
    )


class MDFeProductLotacaoLocal(spec_models.SpecModel):
    _name = "l10n_br_mdfe.inflotacao.local"
    _inherit = ["mdfe.30.inflocalcarrega", "mdfe.30.inflocaldescarrega"]
    _description = "Informações De Localização da Lotação MDFe"

    local_type = fields.Selection(
        selection=[
            ("CEP", "CEP"),
            ("coord", "Coordenadas"),
        ],
        default="CEP",
    )

    mdfe30_choice_tlocal = fields.Selection(
        selection=[("mdfe30_CEP", "CEP"), ("mdfe30_latitude", "Latitude/Longitude")],
        string="Tipo de Local",
        compute="_compute_choice",
    )

    @api.depends("local_type")
    def _compute_choice(self):
        for record in self:
            if record.local_type == "CEP":
                record.mdfe30_choice_tlocal = "mdfe30_CEP"
            else:
                record.mdfe30_choice_tlocal = "mdfe30_latitude"
