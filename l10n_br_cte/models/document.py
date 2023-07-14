# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


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
    _binding_module = "nfelib.cte.bindings.v4_0.cte_v4_00"
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
    # CT-e document fields
    ##########################

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
                and record.document_type.prefix
                and record.document_key
            ):
                record.cte40_Id = "{}{}".format(
                    record.document_type.prefix, record.document_key
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
        related="company_id.partner_id.state_id.ibge_code", string="cte40_cUF"
    )

    cte40_cCT = fields.Char()  # TODO

    cte40_CFOP = fields.Char(compute="_compute_cte40_CFOP")

    cte40_natOp = fields.Char(related="operation_name")

    cte40_mod = fields.Char(related="document_type_id.code", string="cte40_mod")

    cte40_serie = fields.Char(related="document_serie")

    cte40_nCT = fields.Char(related="document_number")

    cte40_dhEmi = fields.Datetime(related="document_date")

    cte40_tpImp = fields.Selection(related="tpImp")

    cte40_tpEmis = fields.Selection(related="cte_transmission")

    cte40_cDV = fields.Char()  # TODO

    cte40_tpAmb = fields.Selection(related="cte_environment")

    cte40_tpCTe = fields.Selection(related="tpCTe")

    cte40_procEmi = fields.Selection(default="0")

    cte40_verProc = fields.Char(
        copy=False,
        default=lambda s: s.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_cte.version.name", default="Odoo Brasil OCA v14"),
    )

    cte40_cMunEnv = fields.Char(
        related="company_id.partner_id.city_id.ibge_code"
    )  # TODO compute pro exterior

    cte40_xMunEnv = fields.Char(
        related="company_id.partner_id.city_id.name"
    )  # TODO compute pro exterior

    cte40_UFEnv = fields.Char(
        related="company_id.partner_id.state_id.code",
        string="nfe40_UFEnv",
    )

    cte40_tpServ = fields.Selection(related="tpServ")

    cte40_indIEToma = fields.Char()  # TODO IE tomador

    cte40_cMunIni = fields.Char(
        related="company_id.partner_id.city_id.ibge_code"
    )  # TODO compute pro exterior

    cte40_xMunIni = fields.Char(
        related="company_id.partner_id.city_id.name"
    )  # TODO compute pro exterior

    cte40_UFIni = fields.Char(
        related="company_id.partner_id.state_id.ibge_code", string="cte40_cUF"
    )

    cte40_cMunFim = fields.Char(related="partner_id.city_id.ibge_code")

    cte40_xMunFim = fields.Char(related="partner_id.city_id.name")

    cte40_UFFim = fields.Char(related="partner_id.state_id.code", string="cte40_cUF")

    cte40_retira = fields.Selection(related="retira")

    cte40_toma4 = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_toma",
        readonly=True,
        string="Tomador de Serviço",
    )  # TODO

    cte40_toma3 = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_toma",
        readonly=True,
        string="Tomador de Serviço",
    )  # TODO

    # View
    retira = fields.Selection(selection=[("0", "Sim"), ("1", "Não")])  # TODO constantes

    # toma = fields.Selection()   # TODO

    tpServ = fields.Selection(
        selection=[
            ("6", "Transporte de Pessoas"),
            ("7", "Transporte de Valores"),
            ("8", "Excesso de Bagagem"),
        ],
    )

    tpCTe = fields.Selection(
        selection=[
            ("0", "CTe Normal"),
            ("1", "CTe Complementar"),
            ("3", "CTe Substituição"),
        ],
    )

    cte_environment = fields.Selection(
        selection=[("1", "Produção"), ("2", "Homologação")],
        string="CTe Environment",
        copy=False,
    )

    cte_transmission = fields.Selection(
        selection=[
            ("1", "Normal"),
            ("3", "Regime Especial NFF"),
            ("4", "EPEC pela SVC"),
        ]
    )

    tpImp = fields.Selection(
        selection=[("1", "Retrato"), ("2", "Paisagem")]
    )  # TODO constantes

    ##########################
    # CT-e tag: ide
    # Compute Methods
    ##########################

    def _compute_toma(self):
        for doc in self:
            doc.cte40_toma4 = doc.partner_id

    @api.depends("partner_id", "company_id")
    def _compute_cte40_exterior(self):
        for doc in self:
            if doc.company_id.partner_id.state_id == doc.partner_id.state_id:
                doc.nfe40_idDest = "1"
            elif doc.company_id.partner_id.country_id == doc.partner_id.country_id:
                doc.nfe40_idDest = "2"
            else:
                doc.nfe40_idDest = "3"

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
        comodel_name="res.company",
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
            doc.cte40_rem = doc.company_id

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
    # CT-e tag: receb
    ##########################

    cte40_receb = fields.Many2one(
        comodel_name="res.company",
        compute="_compute_receb_data",
        readonly=True,
        string="Receb",
    )

    ##########################
    # CT-e tag: receb
    # Compute Methods
    ##########################

    def _compute_receb_data(self):
        for doc in self:  # TODO if out
            doc.cte40_receb = doc.company_id

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
            doc.cte40_dest = doc.company_id

    ##########################
    # CT-e tag: vPrest
    ##########################

    cte40_vTPrest = fields.Float(
        string="vTPrest",
    )

    cte40_vRec = fields.Float(
        string="vRec",
    )

    ##########################
    # CT-e tag: infCTeNorm
    ##########################

    cte40_prodPred = fields.Char(string="prodPred")

    # TODO outros níveis infcteNorm

    ##########################
    # CT-e tag: infCteComp
    ##########################
