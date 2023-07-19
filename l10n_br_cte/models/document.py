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
        related="company_id.partner_id.state_id.ibge_code",
        string="cte40_cUF",
        store=True,
    )

    cte40_cCT = fields.Char(related="document_key", store=True)

    cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP",
    )

    cte40_CFOP = fields.Char(related="cfop_id.code", store=True)

    cte40_natOp = fields.Char(related="operation_name", store=True)

    cte40_mod = fields.Char(
        related="document_type_id.code", string="cte40_mod", store=True
    )

    cte40_serie = fields.Char(related="document_serie", store=True)

    cte40_nCT = fields.Char(related="document_number", store=True)

    cte40_dhEmi = fields.Datetime(related="document_date", store=True)

    cte40_tpImp = fields.Selection(related="tpImp", store=True)

    cte40_tpEmis = fields.Selection(related="cte_transmission", store=True)

    cte40_cDV = fields.Char(compute="_compute_cDV", store=True)

    cte40_tpAmb = fields.Selection(related="cte_environment", store=True)

    cte40_tpCTe = fields.Selection(related="tpCTe", store=True)

    cte40_procEmi = fields.Selection(default="0", store=True)

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

    cte40_tpServ = fields.Selection(related="tpServ", store=True)

    cte40_indIEToma = fields.Char(compute="_compute_toma", store=True)

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

    cte40_retira = fields.Selection(related="retira", store=True)

    cte40_toma4 = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_toma",
        readonly=True,
        string="Tomador de Serviço",
    )

    cte40_toma3 = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_toma",
        readonly=True,
        string="Tomador de Serviço",
    )

    ##########################
    # CT-e tag: ide
    # Compute Methods
    ##########################

    def _compute_toma(self):
        for doc in self:
            if doc.service_provider in ["0", "1"]:
                doc.cte40_toma3 = doc.company_id
                doc.cte40_indIEToma = doc.cte40_toma3.inscr_est
                doc.cte40_toma4 = None
            elif doc.service_provider in ["2", "3"]:
                doc.cte40_toma3 = doc.partner_id
                doc.cte40_indIEToma = doc.cte40_toma3.inscr_est
                doc.cte40_toma4 = None
            else:
                doc.cte40_toma3 = None
                doc.cte40_toma4 = doc.partner_id
                doc.cte40_indIEToma = doc.cte40_toma4.inscr_est

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
        store=True,
    )

    cte40_CRT = fields.Selection(
        related="company_tax_framework",
        string="Código de Regime Tributário (CTe)",
        store=True,
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
        store=True,
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
        store=True,
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
        store=True,
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
        store=True,
    )

    ##########################
    # CT-e tag: dest
    # Compute Methods
    ##########################

    def _compute_dest_data(self):
        for doc in self:  # TODO if out
            doc.cte40_dest = doc.partner_id

    ##########################
    # CT-e tag: imp
    ##########################

    cte40_imp = fields.One2many(
        comodel_name="l10n_br_fiscal.document.line", related="fiscal_line_ids"
    )

    #####################################
    # CT-e tag: infCTeNorm and infCteComp
    #####################################

    cte40_choice244 = fields.Selection(
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
        store=True,
    )

    cte40_infCTeNorm = fields.One2many(
        comodel_name="l10n_br_fiscal.document.related",
        inverse_name="document_id",
        compute="_compute_cte_doc",
        store=True,
    )

    cte40_infCTeComp = fields.One2many(
        comodel_name="l10n_br_fiscal.document.related",
        inverse_name="document_id",
        compute="_compute_cte_doc",
        store=True,
    )

    #####################################
    # CT-e tag: infCTeNorm and infCteComp
    # Compute Methods
    #####################################

    @api.depends("document_type_id")
    def _compute_cte_doc(self):
        """Set schema data which are not just related fields"""
        for rec in self:
            if rec.document_type_id:
                if rec.cte40_choice244 == "cte40_infNorm":
                    rec.cte40_infCTeNorm = rec
                elif rec.cte40_choice244 == "cte40_infComp":
                    rec.cte40_infCTeComp = rec

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

    cte40_autXML = fields.One2many(default=_default_cte40_autxml, store=True)

    # View
    retira = fields.Selection(selection=[("0", "Sim"), ("1", "Não")], default="1")

    tpServ = fields.Selection(
        selection=[
            ("6", "Transporte de Pessoas"),
            ("7", "Transporte de Valores"),
            ("8", "Excesso de Bagagem"),
        ],
        default="6",
    )

    tpCTe = fields.Selection(
        selection=[
            ("0", "CTe Normal"),
            ("1", "CTe Complementar"),
            ("3", "CTe Substituição"),
        ],
        default="0",
    )

    cte_environment = fields.Selection(
        selection=[("1", "Produção"), ("2", "Homologação")],
        string="CTe Environment",
        copy=False,
        default="2",
    )

    cte_transmission = fields.Selection(
        selection=[
            ("1", "Normal"),
            ("3", "Regime Especial NFF"),
            ("4", "EPEC pela SVC"),
        ],
        default="1",
    )

    tpImp = fields.Selection(
        selection=[("1", "Retrato"), ("2", "Paisagem")], default="1"
    )
