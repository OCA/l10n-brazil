# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
import string
from datetime import datetime
from enum import Enum
from unicodedata import normalize

from erpbrasil.assinatura import certificado as cert
from erpbrasil.base.fiscal.edoc import ChaveEdoc
from erpbrasil.edoc.mdfe import QR_CODE_URL
from erpbrasil.transmissao import TransmissaoSOAP
from nfelib.mdfe.bindings.v3_0.mdfe_v3_00 import Mdfe
from nfelib.nfe.ws.edoc_legacy import MDFeAdapter as edoc_mdfe
from requests import Session

from odoo import _, api, fields
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    AUTORIZADO,
    CANCELADO,
    CANCELADO_DENTRO_PRAZO,
    CANCELADO_FORA_PRAZO,
    DENEGADO,
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
)
from ..constants.modal import (
    MDFE_MODAL_DEFAULT,
    MDFE_MODAL_DEFAULT_AIRCRAFT,
    MDFE_MODAL_HARBORS,
    MDFE_MODAL_SHIP_TYPES,
    MDFE_MODAL_VERSION_DEFAULT,
    MDFE_MODALS,
)


def filtered_processador_edoc_mdfe(record):
    return (
        record.processador_edoc == PROCESSADOR_OCA
        and record.document_type_id.code == MODELO_FISCAL_MDFE
    )


class MDFe(spec_models.StackedModel):

    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "mdfe.30.tmdfe_infmdfe"]
    _stacked = "mdfe.30.tmdfe_infmdfe"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_tipos_basico_v3_00"
    _field_prefix = "mdfe30_"
    _schema_name = "mdfe"
    _schema_version = "3.0.0"
    _odoo_module = "l10n_br_mdfe"
    _spec_module = "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_tipos_basico_v3_00"
    _spec_tab_name = "MDFe"
    _mdfe_search_keys = ["mdfe30_Id"]

    # all m2o at this level will be stacked even if not required:
    _force_stack_paths = [
        "infmdfe.infAdic",
        "infmdfe.tot",
        "infmdfe.infsolicnff",
        "infmdfe.InfDoc",
    ]

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
    - <infSolicNFF>"""

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
                record.mdfe30_Id = "{}{}".format(
                    record.document_type_id.prefix, record.document_key
                )

    def _inverse_mdfe30_id_tag(self):
        for record in self:
            if record.mdfe30_Id:
                record.document_key = re.findall(r"\d+", str(record.mdfe30_Id))[0]

    ##########################
    # MDF-e tag: ide
    ##########################

    mdfe30_cUF = fields.Selection(compute="_compute_uf", inverse="_inverse_uf")

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
        default=lambda self: self.env.company.mdfe_transp_type,
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
        compute="_compute_initial_final_state", inverse="_inverse_initial_final_state"
    )

    mdfe30_UFFim = fields.Selection(
        compute="_compute_initial_final_state", inverse="_inverse_initial_final_state"
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
        compute="_compute_inf_carrega",
        inverse="_inverse_inf_carrega",
        string="Informações dos Municipios de Carregamento",
    )

    mdfe_loading_city_ids = fields.Many2many(
        comodel_name="res.city", string="Loading Cities"
    )

    mdfe30_infPercurso = fields.One2many(compute="_compute_inf_percurso")

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
    def _compute_uf(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_cUF = record.company_id.partner_id.state_id.ibge_code

    @api.depends("mdfe_initial_state_id", "mdfe_final_state_id")
    def _compute_initial_final_state(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_UFIni = record.mdfe_initial_state_id.code
            record.mdfe30_UFFim = record.mdfe_final_state_id.code

    @api.depends("mdfe_loading_city_ids")
    def _compute_inf_carrega(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_infMunCarrega = [(5, 0, 0)]
            record.mdfe30_infMunCarrega = [
                (
                    0,
                    0,
                    {
                        "mdfe30_cMunCarrega": city.ibge_code,
                        "mdfe30_xMunCarrega": city.name,
                    },
                )
                for city in record.mdfe_loading_city_ids
            ]

    def _inverse_inf_carrega(self):
        for record in self:
            city_ids = self.env["res.city"].search(
                [("ibge_code", "=", record.mdfe30_infMunCarrega.mdfe30_cMunCarrega)]
            )
            if city_ids:
                record.mdfe_loading_city_ids = [(6, 0, city_ids.ids)]

    def _inverse_initial_final_state(self):
        for record in self:
            initial_state_id = self.env["res.country.state"].search(
                [("code", "=", record.mdfe30_UFIni)], limit=1
            )
            final_state_id = self.env["res.country.state"].search(
                [("code", "=", record.mdfe30_UFFim)], limit=1
            )

            if initial_state_id:
                record.mdfe_initial_state_id = initial_state_id

            if final_state_id:
                record.mdfe_final_state_id = final_state_id

    def _inverse_uf(self):
        for record in self:
            state_id = self.env["res.country.state"].search(
                [("code", "=", record.mdfe30_cUF)], limit=1
            )
            if state_id:
                record.company_id.partner_id.state_id = state_id

    @api.depends("mdfe_route_state_ids")
    def _compute_inf_percurso(self):
        for record in self:
            record.mdfe30_infPercurso = [(5, 0, 0)]
            record.mdfe30_infPercurso = [
                (
                    0,
                    0,
                    {
                        "mdfe30_UFPer": state.code,
                    },
                )
                for state in record.mdfe_route_state_ids
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
    modal_aereo_id = fields.Many2one(
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
    modal_aquaviario_id = fields.Many2one(
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
        size=5,
    )

    mdfe30_infTermDescarreg = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.descarregamento",
        inverse_name="document_id",
        size=5,
    )

    mdfe30_infEmbComb = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.comboio",
        inverse_name="document_id",
        size=30,
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
    modal_ferroviario_id = fields.Many2one(
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
    modal_rodoviario_id = fields.Many2one(
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

    mdfe30_infContratante = fields.Many2many(comodel_name="res.partner")

    mdfe30_RNTRC = fields.Char(size=8, string="RNTRC")

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
        size=10,
    )

    mdfe30_cInt = fields.Char(size=10, string="Código do Veículo")

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
        size=3,
    )

    mdfe30_lacRodo = fields.One2many(
        comodel_name="l10n_br_mdfe.transporte.lacre", inverse_name="document_id"
    )

    mdfe30_UF = fields.Selection(selection=TUF, compute="_compute_rodo_uf")

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
    def _compute_rodo_uf(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_UF = record.rodo_vehicle_state_id.code

    def _export_fields_mdfe_30_infmodal(self, xsd_fields, class_obj, export_dict):
        self = self.with_context(module="l10n_br_mdfe")

        if self.mdfe_modal == "1":
            export_dict["any_element"] = self._export_modal_rodoviario()
        elif self.mdfe_modal == "2":
            export_dict["any_element"] = self._export_modal_aereo()
        elif self.mdfe_modal == "3":
            export_dict["any_element"] = self._export_modal_aquaviario()
        elif self.mdfe_modal == "4":
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
        related="mdfe30_lacRodo",
    )

    ##########################
    # MDF-e tag: infDoc
    ##########################

    mdfe30_infMunDescarga = fields.One2many(
        comodel_name="l10n_br_mdfe.municipio.descarga", inverse_name="document_id"
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

    mdfe30_qCTe = fields.Char(compute="_compute_tot")

    mdfe30_qNFe = fields.Char(compute="_compute_tot")

    mdfe30_qMDFe = fields.Char(compute="_compute_tot")

    mdfe30_qCarga = fields.Float(compute="_compute_tot")

    mdfe30_vCarga = fields.Float(compute="_compute_tot")

    mdfe30_cUnid = fields.Selection(default="01")

    ##########################
    # MDF-e tag: tot
    # Methods
    ##########################

    @api.depends(
        "mdfe30_infMunDescarga.cte_ids",
        "mdfe30_infMunDescarga.nfe_ids",
        "mdfe30_infMunDescarga.mdfe_ids",
    )
    def _compute_tot(self):
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

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        if field_name == "mdfe30_infModal":
            return self._build_generateds(class_obj._fields[field_name].comodel_name)

        return super()._export_many2one(field_name, xsd_required, class_obj)

    def _build_attr(self, node, fields, vals, path, attr):
        key = "mdfe30_%s" % (attr[0],)  # TODO schema wise
        value = getattr(node, attr[0])

        if attr[0] == "any_element":  # build modal
            modal_id = self._get_modal_to_build(node.any_element.__module__)
            if modal_id is False:
                return

            modal_attrs = modal_id.build_attrs(value, path=path)
            for chave, valor in modal_attrs.items():
                vals[chave] = valor
            return

        if key == "mdfe30_mod":
            if isinstance(value, Enum):
                value = value.value

            vals["document_type_id"] = (
                self.env["l10n_br_fiscal.document.type"]
                .search([("code", "=", value)], limit=1)
                .id
            )

        return super()._build_attr(node, fields, vals, path, attr)

    def _get_modal_to_build(self, module):
        modal_by_binding_module = {
            self.modal_rodoviario_id._binding_module: self.modal_rodoviario_id,
            self.modal_aereo_id._binding_module: self.modal_aereo_id,
            self.modal_aquaviario_id._binding_module: self.modal_aquaviario_id,
            self.modal_ferroviario_id._binding_module: self.modal_ferroviario_id,
        }
        if module not in modal_by_binding_module:
            return False

        return modal_by_binding_module[module]

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
            super()._build_many2one(
                self.env["res.partner"], vals, new_value, "partner_id", value, path
            )

        else:
            super()._build_many2one(comodel, vals, new_value, key, value, path)

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        if rec_dict.get("mdfe30_Id"):
            domain = [("mdfe30_Id", "=", rec_dict.get("mdfe30_Id"))]
            match = self.search(domain, limit=1)
            if match:
                return match.id
        return False

    ################################
    # Business Model Methods
    ################################

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.with_context(lang="pt_BR").filtered(
            filtered_processador_edoc_mdfe
        ):
            record = record.with_context(module="l10n_br_mdfe")
            inf_mdfe = record.export_ds()[0]

            inf_mdfe_supl = None
            if record.mdfe30_infMDFeSupl:
                inf_mdfe_supl = record.mdfe30_infMDFeSupl.export_ds()[0]

            mdfe = Mdfe(infMDFe=inf_mdfe, infMDFeSupl=inf_mdfe_supl, signature=None)
            edocs.append(mdfe)
        return edocs

    def _processador(self):
        if self.document_type != MODELO_FISCAL_MDFE:
            return super()._processador()

        certificate = False
        if self.company_id.sudo().certificate_nfe_id:
            certificate = self.company_id.sudo().certificate_nfe_id
        elif self.company_id.sudo().certificate_ecnpj_id:
            certificate = self.company_id.sudo().certificate_ecnpj_id

        if not certificate:
            raise UserError(_("Certificado não encontrado"))

        certificado = cert.Certificado(
            arquivo=certificate.file,
            senha=certificate.password,
        )
        session = Session()
        session.verify = False

        params = {
            "transmissao": TransmissaoSOAP(certificado, session),
            "versao": self.mdfe_version,
            "ambiente": self.mdfe_environment,
            "uf": self.company_id.state_id.ibge_code,
        }
        return edoc_mdfe(**params)

    def _generate_key(self):
        super()._generate_key()

        for record in self.filtered(filtered_processador_edoc_mdfe):
            date = fields.Datetime.context_timestamp(record, record.document_date)
            chave_edoc = ChaveEdoc(
                ano_mes=date.strftime("%y%m").zfill(4),
                cnpj_cpf_emitente=record.company_cnpj_cpf,
                codigo_uf=(
                    record.company_state_id and record.company_state_id.ibge_code or ""
                ),
                forma_emissao=int(self.mdfe_transmission),
                modelo_documento=record.document_type_id.code or "",
                numero_documento=record.document_number or "",
                numero_serie=record.document_serie or "",
                validar=False,
            )
            record.key_random_code = chave_edoc.codigo_aleatorio
            record.key_check_digit = chave_edoc.digito_verificador
            record.document_key = chave_edoc.chave

    def _document_cancel(self, justificative):
        result = super(MDFe, self)._document_cancel(justificative)
        online_event = self.filtered(filtered_processador_edoc_mdfe)
        if online_event:
            online_event.cancel_mdfe()
        return result

    def _document_export(self, pretty_print=True):
        result = super()._document_export()
        for record in self.filtered(filtered_processador_edoc_mdfe):
            edoc = record.serialize()[0]
            processador = record._processador()
            xml_file = processador.render_edoc_xsdata(edoc, pretty_print=pretty_print)[
                0
            ]
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
            xml_assinado = processador.assina_raiz(edoc, edoc.infMDFe.Id)
            self._valida_xml(xml_assinado)
        return result

    def _valida_xml(self, xml_file):
        self.ensure_one()

        if self.document_type != MODELO_FISCAL_MDFE:
            return super()._valida_xml(xml_file)

        erros = Mdfe.schema_validation(xml_file)
        erros = "\n".join(erros)
        self.write({"xml_error_message": erros or False})

    def view_pdf(self):
        if not self.filtered(filtered_processador_edoc_mdfe):
            return super().view_pdf()

        return self.action_damdfe_report()

    def atualiza_status_mdfe(self, processo):
        self.ensure_one()

        infProt = processo.resposta.protMDFe.infProt

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
                file_response_xml=processo.processo_xml,
            )
        self.write(
            {
                "status_code": infProt.cStat,
                "status_name": infProt.xMotivo,
            }
        )
        self._change_state(state)

    def _eletronic_document_send(self):
        super(MDFe, self)._eletronic_document_send()
        for record in self.filtered(filtered_processador_edoc_mdfe):
            if record.xml_error_message:
                return

            processador = record._processador()
            for edoc in record.serialize():
                processo = None
                for p in processador.processar_documento(edoc):
                    processo = p
                    if processo.webservice == "mdfeRecepcaoLote":
                        record.authorization_event_id._save_event_file(
                            processo.envio_xml, "xml"
                        )

            if processo.resposta.cStat in LOTE_PROCESSADO + ["100"]:
                record.atualiza_status_mdfe(processo)

            elif processo.resposta.cStat in DENEGADO:
                record._change_state(SITUACAO_EDOC_DENEGADA)
                record.write(
                    {
                        "status_code": processo.resposta.cStat,
                        "status_name": processo.resposta.xMotivo,
                    }
                )

            else:
                record._change_state(SITUACAO_EDOC_REJEITADA)
                record.write(
                    {
                        "status_code": processo.resposta.cStat,
                        "status_name": processo.resposta.xMotivo,
                    }
                )

    def cancel_mdfe(self):
        self.ensure_one()
        processador = self._processador()

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
            xml_file=processo.envio_xml.decode("utf-8"),
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
        processador = self._processador()

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
            xml_file=processo.envio_xml.decode("utf-8"),
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

    def action_document_closure(self):
        self.ensure_one()
        if self.state_edoc != SITUACAO_EDOC_AUTORIZADA:
            raise UserError(_("You cannot close the document if it's not authorized."))

        return self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_br_mdfe.document_closure_wizard_action"
        )

    def _document_qrcode(self):
        super()._document_qrcode()

        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_infMDFeSupl = self.env[
                "l10n_br_fiscal.document.supplement"
            ].create({"qrcode": record.get_mdfe_qrcode()})

    def get_mdfe_qrcode(self):
        if self.document_type != MODELO_FISCAL_MDFE:
            return

        processador = self._processador()
        if self.mdfe_transmission == "1":
            return processador.monta_qrcode(self.document_key)

        serialized_doc = self.serialize()[0]
        xml = processador.assina_raiz(serialized_doc, serialized_doc.infMDFe.Id)
        return processador.monta_qrcode_contingencia(serialized_doc, xml)

    def action_damdfe_report(self):
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", "l10n_br_mdfe.report_damdfe")],
                limit=1,
            )
            .report_action(self.id, data=self._prepare_damdfe_values())
        )

    def _prepare_damdfe_values(self):
        return {
            "company_id": self.company_id.id,
            "company_has_logo": bool(self.company_id.logo),
            "company_ie": self.company_id.inscr_est,
            "company_logo": self.company_id.inscr_est,
            "company_cnpj": self.company_id.cnpj_cpf,
            "company_legal_name": self.company_id.legal_name,
            "company_street": self.company_id.street,
            "company_number": self.company_id.street_number,
            "company_district": self.company_id.district,
            "company_city": self.company_id.city_id.display_name,
            "company_state": self.company_id.state_id.code,
            "company_zip": self.company_id.zip,
            "uf_carreg": self.mdfe_initial_state_id.code,
            "uf_descarreg": self.mdfe_final_state_id.code,
            "qt_cte": self.mdfe30_qCTe,
            "qt_nfe": self.mdfe30_qNFe,
            "qt_mdfe": self.mdfe30_qMDFe,
            "total_weight": self.mdfe30_qCarga,
            "weight_measure": "KG" if self.mdfe30_cUnid == "01" else "TON",
            "qr_code_url": QR_CODE_URL,
            "document_key": self._format_document_key(self.document_key),
            "document_number": self.document_number,
            "document_model": self.document_type,
            "document_serie": self.document_serie_id.code,
            "document_date": self.document_date.astimezone().strftime(
                "%d/%m/%y %H:%M:%S"
            ),
            "fiscal_additional_data": self.fiscal_additional_data,
            "customer_additional_data": self.customer_additional_data,
            "authorization_protocol": self.authorization_protocol,
            "contingency": self.mdfe_transmission != "1",
            "environment": self.mdfe_environment,
            "qr_code": self.get_mdfe_qrcode(),
            "document_info": self.mdfe30_infMunDescarga._prepare_damdfe_values(),
            "modal": self.mdfe_modal,
            "modal_str": self._get_modal_str(),
            "modal_aereo_data": self.modal_aereo_id._prepare_damdfe_values(),
            "modal_rodoviario_data": self.modal_rodoviario_id._prepare_damdfe_values(),
            "modal_aquaviario_data": self.modal_aquaviario_id._prepare_damdfe_values(),
            "modal_ferroviario_data": self.modal_ferroviario_id._prepare_damdfe_values(),
        }

    @api.model
    def _get_modal_str(self):
        MODAL_TO_STR = {
            "1": "Rodoviário",
            "2": "Aéreo",
            "3": "Aquaviário",
            "4": "Ferroviário",
        }
        return MODAL_TO_STR[self.mdfe_modal]

    @api.model
    def _format_document_key(self, key):
        pace = 4
        formatted_key = ""
        for i in range(0, len(key), pace):
            formatted_key += key[i : i + pace] + " "

        return formatted_key
