# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK_SIMPLES_ALL
from odoo.addons.spec_driven_model.models import spec_models


class L10nBrFiscalDocumentLine(spec_models.SpecModel):
    _name = "l10n_br_fiscal.document.line"
    _inherit = [
        "l10n_br_fiscal.document.line",
        # serv
        "nfse.10.tcserv",
        "nfse.10.tclocprest",
        "nfse.10.tccserv",
        # valores
        "nfse.10.tcinfovalores",
        "nfse.10.tcvservprest",
        "nfse.10.tcvdesccondincond",
        "nfse.10.tcinfotributacao",
        "nfse.10.tctribmunicipal",
        "nfse.10.tctribnacional",
        "nfse.10.tctriboutrospiscofins",
        "nfse.10.tctribtotal",
    ]

    _nfse10_odoo_module = (
        "odoo.addons.l10n_br_nfse_spec.models.v1_0.tipos_complexos_v1_00"
    )
    _nfse10_binding_module = "nfelib.nfse.bindings.v1_0.tipos_complexos_v1_00"
    _nfse10_binding_type_serv = "Tcserv"
    _nfse10_binding_type_valores = "TcinfoValores"
    _nfse10_binding_type_vServPrest = "TcvservPrest"
    _nfse10_binding_type_vDescCondIncond = "TcvdescCondIncond"
    _nfse10_binding_type_trib = "TcinfoTributacao"  # TODO sure?
    _nfse10_binding_type_piscofins = "TctribOutrosPisCofins"
    _nfse10_binding_type_locPrest = "TclocPrest"
    _nfse10_binding_type_cServ = "Tccserv"
    _nfse10_binding_type_tribMun = "TctribMunicipal"
    _nfse10_binding_type_tribFed = "TctribNacional"
    _nfse10_binding_type_totTrib = "TctribTotal"

    nfse10_locPrest = fields.Many2one(
        "l10n_br_fiscal.document.line",
        compute="_compute_nfse10_self",
        string="Local Prestação",
    )
    nfse10_cServ = fields.Many2one(
        "l10n_br_fiscal.document.line",
        compute="_compute_nfse10_self",
        string="Código Serviço",
    )
    nfse10_vServPrest = fields.Many2one(
        "l10n_br_fiscal.document.line",
        compute="_compute_nfse10_self",
        string="Valores Serviço",
    )
    nfse10_vDescCondIncond = fields.Many2one(
        "l10n_br_fiscal.document.line",
        compute="_compute_nfse10_self",
        string="Descontos",
    )
    nfse10_trib = fields.Many2one(
        "l10n_br_fiscal.document.line",
        compute="_compute_nfse10_self",
        string="Tributação",
    )
    nfse10_tribMun = fields.Many2one(
        "l10n_br_fiscal.document.line",
        compute="_compute_nfse10_self",
        string="Tributos Municipais",
    )
    nfse10_tribFed = fields.Many2one(
        "l10n_br_fiscal.document.line",
        compute="_compute_nfse10_self",
        string="Tributos Federais",
    )
    nfse10_piscofins = fields.Many2one(
        "l10n_br_fiscal.document.line",
        compute="_compute_nfse10_self",
        string="PIS/COFINS",
    )
    nfse10_totTrib = fields.Many2one(
        "l10n_br_fiscal.document.line",
        compute="_compute_nfse10_self",
        string="Total Tributos",
    )

    # Fields mapped to tags
    nfse10_cLocPrestacao = fields.Char(related="issqn_fg_city_id.ibge_code")
    nfse10_cTribNac = fields.Char(related="national_taxation_code_id.code")
    nfse10_cTribMun = fields.Char(related="city_taxation_code_id.code")
    nfse10_cNBS = fields.Char(related="nbs_id.code")
    nfse10_xDescServ = fields.Char(related="name")

    nfse10_vServ = fields.Char(compute="_compute_nfse10_valores")
    nfse10_vDescIncond = fields.Char(compute="_compute_nfse10_valores")
    nfse10_vDescCond = fields.Char(compute="_compute_nfse10_valores")

    nfse10_tribISSQN = fields.Selection(default="1")
    nfse10_tpRetISSQN = fields.Selection(compute="_compute_nfse10_trib_mun")
    nfse10_pAliq = fields.Char(compute="_compute_nfse10_trib_mun")

    nfse10_vRetCP = fields.Char(compute="_compute_nfse10_trib_fed")
    nfse10_vRetIRRF = fields.Char(compute="_compute_nfse10_trib_fed")
    nfse10_vRetCSLL = fields.Char(compute="_compute_nfse10_trib_fed")

    nfse10_CST = fields.Selection(compute="_compute_nfse10_pis_cofins")
    nfse10_vBCPisCofins = fields.Char(compute="_compute_nfse10_pis_cofins")
    nfse10_pAliqPis = fields.Char(compute="_compute_nfse10_pis_cofins")
    nfse10_pAliqCofins = fields.Char(compute="_compute_nfse10_pis_cofins")
    nfse10_vPis = fields.Char(compute="_compute_nfse10_pis_cofins")
    nfse10_vCofins = fields.Char(compute="_compute_nfse10_pis_cofins")
    nfse10_tpRetPisCofins = fields.Selection(compute="_compute_nfse10_pis_cofins")

    nfse10_indTotTrib = fields.Selection(compute="_compute_nfse10_tot_trib")
    nfse10_pTotTribSN = fields.Char(compute="_compute_nfse10_tot_trib")

    def _compute_nfse10_self(self):
        for rec in self:
            rec.nfse10_locPrest = rec.id
            rec.nfse10_cServ = rec.id
            rec.nfse10_vServPrest = rec.id
            rec.nfse10_vDescCondIncond = rec.id
            rec.nfse10_trib = rec.id
            rec.nfse10_tribMun = rec.id
            rec.nfse10_tribFed = rec.id
            rec.nfse10_piscofins = rec.id
            rec.nfse10_totTrib = rec.id

    @api.depends("price_gross", "discount_value", "issqn_desc_cond_amount")
    def _compute_nfse10_valores(self):
        for rec in self:
            rec.nfse10_vServ = f"{rec.price_gross:.2f}" if rec.price_gross else False
            rec.nfse10_vDescIncond = (
                f"{rec.discount_value:.2f}" if rec.discount_value else False
            )
            rec.nfse10_vDescCond = (
                f"{rec.issqn_desc_cond_amount:.2f}"
                if rec.issqn_desc_cond_amount
                else False
            )

    @api.depends("issqn_percent", "issqn_wh_percent", "issqn_value", "issqn_wh_value")
    def _compute_nfse10_trib_mun(self):
        for rec in self:
            aliquota = rec.issqn_percent or rec.issqn_wh_percent or 0.0
            rec.nfse10_pAliq = f"{aliquota:.2f}" if aliquota > 0 else False
            rec.nfse10_tpRetISSQN = "2" if rec.issqn_wh_value > 0 else "1"

    @api.depends("inss_wh_value", "irpj_wh_value", "csll_wh_value")
    def _compute_nfse10_trib_fed(self):
        for rec in self:
            rec.nfse10_vRetCP = (
                f"{rec.inss_wh_value:.2f}" if rec.inss_wh_value else False
            )
            rec.nfse10_vRetIRRF = (
                f"{rec.irpj_wh_value:.2f}" if rec.irpj_wh_value else False
            )
            rec.nfse10_vRetCSLL = (
                f"{rec.csll_wh_value:.2f}" if rec.csll_wh_value else False
            )

    @api.depends(
        "pis_cst_code",
        "pis_base",
        "cofins_base",
        "pis_percent",
        "cofins_percent",
        "pis_value",
        "cofins_value",
        "pis_wh_value",
        "cofins_wh_value",
    )
    def _compute_nfse10_pis_cofins(self):
        valid_cst = dict(self._fields["nfse10_CST"].selection)
        for rec in self:
            cst = rec.pis_cst_code
            rec.nfse10_CST = cst if cst in valid_cst else "00"
            base = rec.pis_base or rec.cofins_base or 0.0
            rec.nfse10_vBCPisCofins = f"{base:.2f}" if base else False
            rec.nfse10_pAliqPis = f"{rec.pis_percent:.2f}" if rec.pis_percent else False
            rec.nfse10_pAliqCofins = (
                f"{rec.cofins_percent:.2f}" if rec.cofins_percent else False
            )
            rec.nfse10_vPis = f"{rec.pis_value:.2f}" if rec.pis_value else False
            rec.nfse10_vCofins = (
                f"{rec.cofins_value:.2f}" if rec.cofins_value else False
            )
            rec.nfse10_tpRetPisCofins = (
                "1" if (rec.pis_wh_value or rec.cofins_wh_value) else "2"
            )

    @api.depends("company_id.tax_framework")
    def _compute_nfse10_tot_trib(self):
        for rec in self:
            if rec.company_id.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
                rec.nfse10_indTotTrib = False
                rec.nfse10_pTotTribSN = "0.01"
            else:
                rec.nfse10_indTotTrib = "0"
                rec.nfse10_pTotTribSN = False

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        internal_stack_mappings = [
            "nfse10_locPrest",
            "nfse10_cServ",
            "nfse10_vServPrest",
            "nfse10_vDescCondIncond",
            "nfse10_trib",
            "nfse10_tribMun",
            "nfse10_tribFed",
            "nfse10_piscofins",
            "nfse10_totTrib",
        ]
        if field_name in internal_stack_mappings:
            return self._build_binding(
                class_name=class_obj._fields[field_name].comodel_name,
                field_name=field_name,
            )
        return super()._export_many2one(field_name, xsd_required, class_obj)
