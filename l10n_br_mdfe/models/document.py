# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import re
import string
from enum import Enum
from unicodedata import normalize

from erpbrasil.base.fiscal.edoc import ChaveEdoc
from erpbrasil.base.misc import punctuation_rm
from erpbrasil.transmissao import TransmissaoSOAP
from nfelib.mdfe.bindings.v3_0.mdfe_v3_00 import Mdfe
from nfelib.nfe.ws.edoc_legacy import MDFeAdapter as edoc_mdfe
from requests import Session

from odoo import Command, api, fields

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    MODELO_FISCAL_MDFE,
    PROCESSADOR_OCA,
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

    def _inverse_mdfe30_uf(self):
        for record in self:
            state_id = self.env["res.country.state"].search(
                [("code", "=", record.mdfe30_cUF)], limit=1
            )
            if state_id:
                record.company_id.partner_id.state_id = state_id

    @api.depends("mdfe_route_state_ids")
    def _compute_mdfe30_inf_percurso(self):
        for record in self:
            record.mdfe30_infPercurso = [Command.clear()]
            record.mdfe30_infPercurso = [
                Command.create(
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

    mdfe30_qCTe = fields.Char(compute="_compute_mdfe30_tot")

    mdfe30_qNFe = fields.Char(compute="_compute_mdfe30_tot")

    mdfe30_qMDFe = fields.Char(compute="_compute_mdfe30_tot")

    mdfe30_qCarga = fields.Float(compute="_compute_mdfe30_tot")

    mdfe30_vCarga = fields.Float(compute="_compute_mdfe30_tot")

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

    ################################
    # Framework Spec model's methods
    ################################

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

    def _build_attr(self, node, fields, vals, path, attr):
        key = f"mdfe30_{attr[0]}"
        value = getattr(node, attr[0])

        # if attr[0] == "any_element":  # build modal
        #     modal_id = self._get_mdfe_modal_to_build(node.any_element.__module__)
        #     if modal_id is False:
        #         return

        #     modal_attrs = modal_id.build_attrs(value, path=path)
        #     for chave, valor in modal_attrs.items():
        #         vals[chave] = valor
        #     return

        if key == "mdfe30_mod":
            if isinstance(value, Enum):
                value = value.value

            vals["document_type_id"] = (
                self.env["l10n_br_fiscal.document.type"]
                .search([("code", "=", value)], limit=1)
                .id
            )

        return super()._build_attr(node, fields, vals, path, attr)

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
            "transmissao": TransmissaoSOAP(certificado, session),
            "uf": self.company_id.state_id.ibge_code,
            "versao": self.mdfe_version,
            "ambiente": self.mdfe_environment,
        }
        return edoc_mdfe(**params)

    def _generate_key(self):
        if self.document_type_id.code not in [MODELO_FISCAL_MDFE]:
            return super()._generate_key()

        for record in self.filtered(filtered_processador_edoc_mdfe):
            date = fields.Datetime.context_timestamp(record, record.document_date)
            chave_edoc = ChaveEdoc(
                ano_mes=date.strftime("%y%m").zfill(4),
                cnpj_cpf_emitente=record.company_id.vat,
                codigo_uf=(
                    record.company_id.state_id
                    and record.company_id.state_id.ibge_code
                    or ""
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

    def _document_export(self, pretty_print=True):
        result = super()._document_export()
        for record in self.filtered(filtered_processador_edoc_mdfe):
            edoc = record.serialize()[0]
            processador = record._edoc_processor()
            xml_file = processador.render_edoc_xsdata(edoc, pretty_print=pretty_print)[
                0
            ]
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
        pdf_data = report._render_qweb_pdf(
            "main_template_damdfe", self.fiscal_line_ids.document_id.ids
        )
        attachment_data["datas"] = base64.b64encode(pdf_data[0])
        file_pdf = self.file_report_id
        self.file_report_id = False
        file_pdf.unlink()

        self.file_report_id = self.env["ir.attachment"].create(attachment_data)
