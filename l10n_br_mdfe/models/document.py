# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from datetime import datetime, timedelta, timezone
from unicodedata import normalize

from erpbrasil.assinatura import certificado as cert
from erpbrasil.base.fiscal.edoc import ChaveEdoc
from erpbrasil.transmissao import TransmissaoSOAP
from nfelib.mdfe.bindings.v3_0.mdfe_modal_aereo_v3_00 import Aereo
from nfelib.mdfe.bindings.v3_0.mdfe_modal_aquaviario_v3_00 import Aquav
from nfelib.mdfe.bindings.v3_0.mdfe_modal_ferroviario_v3_00 import Ferrov
from nfelib.mdfe.bindings.v3_0.mdfe_modal_rodoviario_v3_00 import Rodo
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
    _force_stack_paths = ["infmdfe.infAdic", "infmdfe.tot", "infmdfe.infsolicnff"]

    INFMDFE_TREE = """
    > <infMDFe>
        > <ide>
        - <emit> res.company
        - <infModal>
        - <infDoc> l10n_br_fiscal.document.related
        > <tot>
    """

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
            if (
                record.document_type_id
                and record.document_type_id.prefix
                and record.document_key
            ):
                record.mdfe30_Id = "{}{}".format(
                    record.document_type_id.prefix, record.document_key
                )
            else:
                record.mdfe30_Id = False

    def _inverse_mdfe30_id_tag(self):
        for record in self:
            if record.mdfe30_Id:
                record.document_key = re.findall(r"\d+", str(record.mdfe30_Id))[0]

    ##########################
    # MDF-e tag: ide
    ##########################

    mdfe30_cUF = fields.Selection(compute="_compute_uf")

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

    mdfe30_UFIni = fields.Selection(compute="_compute_initial_final_state")

    mdfe30_UFFim = fields.Selection(compute="_compute_initial_final_state")

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

    mdfe30_cMDF = fields.Char(related="key_random_code")

    mdfe30_cDV = fields.Char(related="key_check_digit")

    mdfe30_infMunCarrega = fields.One2many(compute="_compute_inf_carrega")

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

    @api.depends("mdfe_route_state_ids")
    def _compute_inf_percurso(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
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

    mdfe30_infModal = fields.Many2one(
        comodel_name="l10n_br_mdfe.modal",
        string="Modal Info",
        compute="_compute_modal_inf",
    )

    mdfe30_versaoModal = fields.Char(related="mdfe30_infModal.mdfe30_versaoModal")

    # Campos do Modal Aéreo
    airplane_nationality = fields.Char(size=4)

    airplane_registration = fields.Char(size=6)

    flight_number = fields.Char(size=9)

    flight_date = fields.Date()

    boarding_airfield = fields.Char(default=MDFE_MODAL_DEFAULT_AIRCRAFT, size=4)

    landing_airfield = fields.Char(default=MDFE_MODAL_DEFAULT_AIRCRAFT, size=4)

    # Campos do Modal Aquaviário
    ship_irin = fields.Char(size=10)

    ship_type = fields.Selection(selection=MDFE_MODAL_SHIP_TYPES)

    ship_code = fields.Char(size=10)

    ship_name = fields.Char(size=60)

    ship_travel_number = fields.Char()

    ship_boarding_point = fields.Selection(selection=MDFE_MODAL_HARBORS)

    ship_landing_point = fields.Selection(selection=MDFE_MODAL_HARBORS)

    transshipment_port = fields.Char(size=60)

    ship_navigation_type = fields.Selection(selection=AQUAV_TPNAV)

    ship_loading_ids = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.carregamento",
        inverse_name="document_id",
        size=5,
    )

    ship_unloading_ids = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.descarregamento",
        inverse_name="document_id",
        size=5,
    )

    ship_convoy_ids = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.comboio",
        inverse_name="document_id",
        size=30,
    )

    ship_empty_load_ids = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.carga.vazia",
        inverse_name="document_id",
    )

    ship_empty_transport_ids = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.transporte.vazio",
        inverse_name="document_id",
    )

    # Campos do Modal Ferroviário
    train_prefix = fields.Char(string="Train Prefix", size=10)

    train_release_time = fields.Datetime(string="Train Release Time")

    train_origin = fields.Char(string="Train Origin", size=3)

    train_destiny = fields.Char(string="Train Destiny", size=3)

    train_wagon_quantity = fields.Char(string="Train Wagon Quantity")

    train_wagon_ids = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.ferroviario.vagao", inverse_name="document_id"
    )

    # Campos do Modal Rodoviário
    rodo_scheduling_code = fields.Char(string="Scheduling Code", size=16)

    rodo_ciot_ids = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.ciot", inverse_name="document_id"
    )

    rodo_toll_device_ids = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.vale_pedagio.dispositivo",
        inverse_name="document_id",
    )

    rod_toll_vehicle_categ = fields.Selection(selection=VALEPED_CATEGCOMBVEIC)

    rodo_contractor_ids = fields.Many2many(comodel_name="res.partner")

    rodo_RNTRC = fields.Char(size=8)

    rodo_payment_ids = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.pagamento",
        inverse_name="document_id",
    )

    rodo_vehicle_proprietary_id = fields.Many2one(comodel_name="res.partner")

    rodo_vehicle_conductor_ids = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.veiculo.condutor",
        inverse_name="document_id",
        size=10,
    )

    rodo_vehicle_code = fields.Char(size=10)

    rodo_vehicle_RENAVAM = fields.Char(size=11)

    rodo_vehicle_plate = fields.Char()

    rodo_vehicle_tare_weight = fields.Char()

    rodo_vehicle_kg_capacity = fields.Char()

    rodo_vehicle_m3_capacity = fields.Char()

    rodo_vehicle_tire_type = fields.Selection(selection=VEICTRACAO_TPROD)

    rodo_vehicle_type = fields.Selection(selection=VEICTRACAO_TPCAR)

    rodo_vehicle_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="Vehicle State",
        domain=[("country_id.code", "=", "BR")],
    )

    rodo_tow_ids = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.rodoviario.reboque",
        inverse_name="document_id",
        size=3,
    )

    rodo_seal_ids = fields.One2many(
        comodel_name="l10n_br_mdfe.transporte.lacre", inverse_name="document_id"
    )

    ##########################
    # MDF-e tag: infModal
    # Methods
    ##########################

    @api.depends("mdfe_modal")
    def _compute_modal_inf(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_infModal = self.env.ref(
                "l10n_br_mdfe.modal_%s" % record.mdfe_modal
            )

    def _export_fields_mdfe_30_infmodal(self, xsd_fields, class_obj, export_dict):
        if self.mdfe_modal == "1":
            export_dict["any_element"] = self._export_modal_rodoviario_fields()
        elif self.mdfe_modal == "2":
            export_dict["any_element"] = self._export_modal_aereo_fields()
        elif self.mdfe_modal == "3":
            export_dict["any_element"] = self._export_modal_aquaviario_fields()
        elif self.mdfe_modal == "4":
            export_dict["any_element"] = self._export_modal_ferroviario_fields()

    def _export_modal_aereo_fields(self):
        return Aereo(
            nac=self.airplane_nationality,
            matr=self.airplane_registration,
            nVoo=self.flight_number,
            cAerEmb=self.boarding_airfield,
            cAerDes=self.landing_airfield,
            dVoo=fields.Date.to_string(self.flight_date),
        )

    def _export_modal_aquaviario_fields(self):
        optional_data = {}
        if self.ship_loading_ids:
            optional_data["infTermCarreg"] = self.ship_loading_ids.export_fields_multi()

        if self.ship_unloading_ids:
            optional_data[
                "infTermDescarreg"
            ] = self.ship_unloading_ids.export_fields_multi()

        if self.ship_convoy_ids:
            optional_data["infEmbComb"] = self.ship_convoy_ids.export_fields_multi()

        if self.ship_empty_load_ids:
            optional_data[
                "infUnidCargaVazia"
            ] = self.ship_empty_load_ids.export_fields_multi()

        if self.ship_empty_transport_ids:
            optional_data[
                "infUnidTranspVazia"
            ] = self.ship_empty_transport_ids.export_fields_multi()

        if self.transshipment_port:
            optional_data["prtTrans"] = self.transshipment_port

        if self.ship_navigation_type:
            optional_data["tpNav"] = self.ship_navigation_type

        return Aquav(
            irin=self.ship_irin,
            tpEmb=self.ship_type,
            cEmbar=self.ship_code,
            xEmbar=self.ship_name,
            cPrtEmb=self.ship_boarding_point,
            cPrtDest=self.ship_landing_point,
            nViag=self.ship_travel_number,
            **optional_data,
        )

    def _export_modal_ferroviario_fields(self):
        train_optional_data = {}
        if self.train_release_time:
            train_optional_data["dhTrem"] = (
                datetime.strftime(self.train_release_time, "%Y-%m-%dT%H:%M:%S")
                + str(timezone(timedelta(hours=-3)))[3:]
            )

        return Ferrov(
            trem=Ferrov.Trem(
                xPref=self.train_prefix,
                xOri=self.train_origin,
                xDest=self.train_destiny,
                qVag=self.train_wagon_quantity,
                **train_optional_data,
            ),
            vag=self.train_wagon_ids.export_fields_multi(),
        )

    def _export_modal_rodoviario_fields(self):
        optional_data = {}
        if self.rodo_scheduling_code:
            optional_data["codAgPorto"] = self.rodo_scheduling_code

        if self.rodo_seal_ids:
            optional_data["lacRodo"] = self.rodo_seal_ids.export_fields_multi(
                Rodo.LacRodo
            )

        if self.rodo_tow_ids:
            optional_data["veicReboque"] = self.rodo_tow_ids.export_fields_multi()

        has_antt_data = any(
            [
                self.rodo_RNTRC,
                self.rodo_ciot_ids,
                self.rodo_toll_device_ids,
                self.rod_toll_vehicle_categ,
                self.rodo_contractor_ids,
                self.rodo_payment_ids,
            ]
        )
        if has_antt_data:
            optional_data["infANTT"] = self._export_modal_rodoviario_antt_fields()

        veic_optional_data = {}
        if self.rodo_vehicle_code:
            veic_optional_data["cInt"] = self.rodo_vehicle_code

        if self.rodo_vehicle_RENAVAM:
            veic_optional_data["RENAVAM"] = self.rodo_vehicle_RENAVAM

        if self.rodo_vehicle_kg_capacity:
            veic_optional_data["capKG"] = self.rodo_vehicle_kg_capacity

        if self.rodo_vehicle_m3_capacity:
            veic_optional_data["capM3"] = self.rodo_vehicle_m3_capacity

        if self.rodo_vehicle_proprietary_id:
            veic_optional_data[
                "prop"
            ] = self.rodo_vehicle_proprietary_id.export_proprietary_fields(
                Rodo.VeicTracao.Prop
            )

        if self.rodo_vehicle_m3_capacity:
            veic_optional_data["capM3"] = self.rodo_vehicle_m3_capacity

        if self.rodo_vehicle_state_id:
            veic_optional_data["UF"] = self.rodo_vehicle_state_id.code

        if self.rodo_vehicle_conductor_ids:
            veic_optional_data[
                "condutor"
            ] = self.rodo_vehicle_conductor_ids.export_fields_multi()

        return Rodo(
            veicTracao=Rodo.VeicTracao(
                placa=self.rodo_vehicle_plate,
                tara=self.rodo_vehicle_tare_weight,
                tpRod=self.rodo_vehicle_tire_type,
                tpCar=self.rodo_vehicle_type,
                **veic_optional_data,
            ),
            **optional_data,
        )

    def _export_modal_rodoviario_antt_fields(self):
        antt_data = {}
        if self.rodo_RNTRC:
            antt_data["RNTRC"] = self.rodo_RNTRC

        if self.rodo_ciot_ids:
            antt_data["infCIOT"] = self.rodo_ciot_ids.export_fields_multi()

        if self.rodo_contractor_ids:
            antt_data[
                "infContratante"
            ] = self.rodo_contractor_ids.export_contractor_fields()

        if self.rodo_payment_ids:
            antt_data["infPag"] = self.rodo_payment_ids.export_fields_multi()

        has_vale_ped_data = self.rodo_toll_device_ids or self.rod_toll_vehicle_categ
        if has_vale_ped_data:
            antt_data["valePed"] = self._export_modal_rodoviario_vale_ped_fields()

        return Rodo.InfAntt(**antt_data)

    def _export_modal_rodoviario_vale_ped_fields(self):
        vale_ped_data = {}
        if self.rodo_toll_device_ids:
            vale_ped_data["disp"] = self.rodo_toll_device_ids.export_fields_multi()

        if self.rod_toll_vehicle_categ:
            vale_ped_data["categCombVeic"] = self.rod_toll_vehicle_categ

        return Rodo.InfAntt.ValePed(**vale_ped_data)

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
        related="rodo_seal_ids",
    )

    ##########################
    # MDF-e tag: infDoc
    ##########################

    mdfe30_infDoc = fields.One2many(
        comodel_name="l10n_br_mdfe.document.info", compute="_compute_doc_inf"
    )

    unloading_city_ids = fields.One2many(
        comodel_name="l10n_br_mdfe.municipio.descarga", inverse_name="document_id"
    )

    ##########################
    # MDF-e tag: infDoc
    # Methods
    ##########################

    @api.depends("unloading_city_ids")
    def _compute_doc_inf(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_infDoc = [(5, 0, 0)]
            record.mdfe30_infDoc = [
                (
                    0,
                    0,
                    {"mdfe30_infMunDescarga": [(6, 0, record.unloading_city_ids.ids)]},
                )
            ]

    ##########################
    # MDF-e tag: infRespTec
    ##########################

    mdfe30_infRespTec = fields.Many2one(
        comodel_name="res.partner",
        related="company_id.technical_support_id",
    )

    ##########################
    # NF-e tag: infAdic
    ##########################

    mdfe30_infAdFisco = fields.Char(compute="_compute_mdfe30_additional_data")

    mdfe30_infCpl = fields.Char(compute="_compute_mdfe30_additional_data")

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

    mdfe30_cUnid = fields.Selection(default="01")

    mdfe30_vCarga = fields.Monetary(compute="_compute_tot_carga")

    mdfe30_qCarga = fields.Float(compute="_compute_tot_carga")

    ##########################
    # MDF-e tag: tot
    # Methods
    ##########################

    @api.depends("unloading_city_ids")
    def _compute_tot(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            cte_qty = len(record.unloading_city_ids.mapped("cte_ids"))
            nfe_qty = len(record.unloading_city_ids.mapped("nfe_ids"))
            mdfe_qty = len(record.unloading_city_ids.mapped("mdfe_ids"))

            record.mdfe30_qCTe = cte_qty and cte_qty or False
            record.mdfe30_qNFe = nfe_qty and nfe_qty or False
            record.mdfe30_qMDFe = mdfe_qty and mdfe_qty or False

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

    @api.depends("mdfe30_cUnid")
    def _compute_tot_carga(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            # TODO: calcular valores
            record.mdfe30_vCarga = 0
            record.mdfe30_qCarga = 0

    ################################
    # Framework Spec model's methods
    ################################

    def _export_field(self, xsd_field, class_obj, member_spec, export_value=None):
        if xsd_field == "mdfe30_tpAmb":
            self.env.context = dict(self.env.context)
            self.env.context.update({"tpAmb": self[xsd_field]})
        return super()._export_field(xsd_field, class_obj, member_spec, export_value)

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        if field_name == "mdfe30_infModal":
            return self._build_generateds(class_obj._fields[field_name].comodel_name)

        return super()._export_many2one(field_name, xsd_required, class_obj)

    def _build_attr(self, node, fields, vals, path, attr):
        key = "mdfe30_%s" % (attr[0],)  # TODO schema wise
        value = getattr(node, attr[0])

        if key == "mdfe30_mod":
            vals["document_type_id"] = (
                self.env["l10n_br_fiscal.document.type"]
                .search([("code", "=", value)], limit=1)
                .id
            )

        return super()._build_attr(node, fields, vals, path, attr)

    ################################
    # Business Model Methods
    ################################

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.with_context(lang="pt_BR").filtered(
            filtered_processador_edoc_mdfe
        ):
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

    def _document_qrcode(self):
        for record in self.filtered(filtered_processador_edoc_mdfe):
            record.mdfe30_infMDFeSupl = self.env[
                "l10n_br_fiscal.document.supplement"
            ].create({"qrcode": record.get_mdfe_qrcode()})

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
                file_response_xml=processo.processo_xml.decode("utf-8"),
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
                            processo.envio_xml.decode("utf-8"), "xml"
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

    def get_mdfe_qrcode(self):
        if self.document_type != MODELO_FISCAL_MDFE:
            return

        processador = self._processador()
        if self.mdfe_transmission == "1":
            return processador.monta_qrcode(self.document_key)

        serialized_doc = self.serialize()[0]
        xml = processador.assina_raiz(serialized_doc, serialized_doc.infMDFe.Id)
        return processador.monta_qrcode_contingencia(serialized_doc, xml)
