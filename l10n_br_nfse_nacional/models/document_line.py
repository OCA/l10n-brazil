# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK_SIMPLES_ALL
from odoo.addons.spec_driven_model.models import spec_models


def _nfse10_amount(value):
    """Format an amount the way the NFS-e schema expects it (2 decimals).

    The export skips an empty element, so a zero amount stays False.
    """
    return f"{value:.2f}" if value else False


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
        "nfse.10.tctribfederal",
        "nfse.10.tctriboutrospiscofins",
        "nfse.10.tctribtotal",
        "nfse.10.tctribtotalpercent",
    ]

    _nfse10_odoo_module = (
        "odoo.addons.l10n_br_nfse_spec.models.v1_0.tipos_complexos_v1_01"
    )
    _nfse10_binding_module = "nfelib.nfse.bindings.v1_0.tipos_complexos_v1_01"
    _nfse10_binding_type_serv = "Tcserv"
    _nfse10_binding_type_valores = "TcinfoValores"
    _nfse10_binding_type_vServPrest = "TcvservPrest"
    _nfse10_binding_type_vDescCondIncond = "TcvdescCondIncond"
    _nfse10_binding_type_trib = "TcinfoTributacao"  # TODO sure?
    _nfse10_binding_type_piscofins = "TctribOutrosPisCofins"
    _nfse10_binding_type_locPrest = "TclocPrest"
    _nfse10_binding_type_cServ = "Tccserv"
    _nfse10_binding_type_tribMun = "TctribMunicipal"
    _nfse10_binding_type_tribFed = "TctribFederal"
    _nfse10_binding_type_totTrib = "TctribTotal"
    _nfse10_binding_type_pTotTrib = "TctribTotalPercent"

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
    # The NFSe schema patterns only accept the unmasked codes: the fiscal
    # tables store them formatted (17.09.01, 1.1404.43.00) for the UI.
    nfse10_cTribNac = fields.Char(related="national_taxation_code_id.code_unmasked")
    nfse10_cTribMun = fields.Char(related="city_taxation_code_id.code_unmasked")
    nfse10_cNBS = fields.Char(related="nbs_id.code_unmasked")
    nfse10_xDescServ = fields.Char(compute="_compute_nfse10_xDescServ")

    nfse10_vServ = fields.Char(compute="_compute_nfse10_valores")
    nfse10_vDescIncond = fields.Char(compute="_compute_nfse10_valores")
    nfse10_vDescCond = fields.Char(compute="_compute_nfse10_valores")

    nfse10_tribISSQN = fields.Selection(compute="_compute_nfse10_trib_issqn")
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
    nfse10_pTotTrib = fields.Many2one(
        "l10n_br_fiscal.document.line",
        compute="_compute_nfse10_tot_trib",
        string="Percentual Total de Tributos",
    )
    nfse10_pTotTribFed = fields.Char(compute="_compute_nfse10_tot_trib")
    nfse10_pTotTribEst = fields.Char(compute="_compute_nfse10_tot_trib")
    nfse10_pTotTribMun = fields.Char(compute="_compute_nfse10_tot_trib")

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

    def _nfse10_declares_document(self):
        """True when this line carries the single service declared in the DPS.

        The DPS has one serv and one valores group, built from a single line
        (see the document). With the consolidation option on, that line
        reports the amounts of the whole document instead of its own ones.
        """
        self.ensure_one()
        document = self.document_id
        return bool(
            document.nfse_nacional_concat_lines
            and self == document._nfse10_service_line()
        )

    @api.depends(
        "name",
        "product_id",
        "document_id.nfse_nacional_concat_lines",
        "document_id.fiscal_line_ids.name",
        "document_id.fiscal_line_ids.product_id",
    )
    def _compute_nfse10_xDescServ(self):
        """Describe the single DPS service, with the descriptions of the lines.

        xDescServ is required by the schema (max 2000 characters, at least one
        non blank character), so a truncated concatenation is trimmed and the
        description of the line is used as the last resort.
        """
        for rec in self:
            text = rec.name
            if rec._nfse10_declares_document():
                names = [
                    line.name
                    for line in rec.document_id.fiscal_line_ids
                    if line.product_id and line.name
                ]
                text = "\n".join(names)[:2000].rstrip() or rec.name
            rec.nfse10_xDescServ = text

    @api.depends(
        "price_gross",
        "discount_value",
        "issqn_desc_cond_amount",
        "document_id.nfse_nacional_concat_lines",
        "document_id.fiscal_line_ids.price_gross",
        "document_id.fiscal_line_ids.discount_value",
        "document_id.fiscal_line_ids.issqn_desc_cond_amount",
    )
    def _compute_nfse10_valores(self):
        for rec in self:
            price_gross = rec.price_gross
            discount = rec.discount_value
            cond_discount = rec.issqn_desc_cond_amount
            if rec._nfse10_declares_document():
                totals = rec.document_id._nfse10_totals()
                price_gross = totals["price_gross"]
                discount = totals["discount_value"]
                cond_discount = totals["issqn_desc_cond_amount"]
            rec.nfse10_vServ = _nfse10_amount(price_gross)
            rec.nfse10_vDescIncond = _nfse10_amount(discount)
            rec.nfse10_vDescCond = _nfse10_amount(cond_discount)

    @api.depends("issqn_tax_id", "issqn_eligibility")
    def _compute_nfse10_trib_issqn(self):
        # issqn_eligibility defaults to "2" (Não incidência) and is rarely set,
        # so only its explicit export and immunity values are taken from it.
        # Non-incidence (such as the rental of movable goods, STF SV 31) comes
        # from the ISSQN NT tax of the fiscal operation.
        issqn_nt = self.env.ref("l10n_br_fiscal.tax_issqn_nt", False)
        for rec in self:
            if rec.issqn_eligibility == "4":
                rec.nfse10_tribISSQN = "3"
            elif rec.issqn_eligibility == "5":
                rec.nfse10_tribISSQN = "2"
            elif issqn_nt and rec.issqn_tax_id == issqn_nt:
                rec.nfse10_tribISSQN = "4"
            else:
                rec.nfse10_tribISSQN = "1"

    @api.depends(
        "issqn_wh_value",
        "document_id.nfse_nacional_concat_lines",
        "document_id.fiscal_line_ids.issqn_wh_value",
    )
    def _compute_nfse10_trib_mun(self):
        # pAliq is optional in the XSD and, for a municipality that joined the
        # national system, the ADN takes the ISSQN rate from its own municipal
        # parameters. Informing it anyway is refused by business rules such as
        # E0625 (rate informed without ISSQN withholding), so it is left out.
        for rec in self:
            issqn_wh_value = rec.issqn_wh_value
            if rec._nfse10_declares_document():
                totals = rec.document_id._nfse10_totals()
                issqn_wh_value = totals["issqn_wh_value"]
            rec.nfse10_pAliq = False
            rec.nfse10_tpRetISSQN = "2" if issqn_wh_value > 0 else "1"

    @api.depends(
        "inss_wh_value",
        "irpj_wh_value",
        "csll_wh_value",
        "document_id.nfse_nacional_concat_lines",
        "document_id.fiscal_line_ids.inss_wh_value",
        "document_id.fiscal_line_ids.irpj_wh_value",
        "document_id.fiscal_line_ids.csll_wh_value",
    )
    def _compute_nfse10_trib_fed(self):
        for rec in self:
            inss = rec.inss_wh_value
            irpj = rec.irpj_wh_value
            csll = rec.csll_wh_value
            if rec._nfse10_declares_document():
                totals = rec.document_id._nfse10_totals()
                inss = totals["inss_wh_value"]
                irpj = totals["irpj_wh_value"]
                csll = totals["csll_wh_value"]
            rec.nfse10_vRetCP = _nfse10_amount(inss)
            rec.nfse10_vRetIRRF = _nfse10_amount(irpj)
            rec.nfse10_vRetCSLL = _nfse10_amount(csll)

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
        "document_id.nfse_nacional_concat_lines",
        "document_id.fiscal_line_ids.pis_base",
        "document_id.fiscal_line_ids.cofins_base",
        "document_id.fiscal_line_ids.pis_percent",
        "document_id.fiscal_line_ids.cofins_percent",
        "document_id.fiscal_line_ids.pis_value",
        "document_id.fiscal_line_ids.cofins_value",
        "document_id.fiscal_line_ids.cofins_wh_value",
        "document_id.fiscal_line_ids.pis_wh_value",
    )
    def _compute_nfse10_pis_cofins(self):
        valid_cst = dict(self._fields["nfse10_CST"].selection)
        for rec in self:
            cst = rec.pis_cst_code
            base = rec.pis_base or rec.cofins_base or 0.0
            pis_percent = rec.pis_percent
            cofins_percent = rec.cofins_percent
            pis = rec.pis_value
            cofins = rec.cofins_value
            withheld = rec.pis_wh_value or rec.cofins_wh_value
            if rec._nfse10_declares_document():
                document = rec.document_id
                totals = document._nfse10_totals()
                base = totals["pis_base"]
                pis = totals["pis_value"]
                cofins = totals["cofins_value"]
                withheld = totals["pis_wh_value"] or totals["cofins_wh_value"]
                pis_percent = document._nfse10_weighted_percent(("pis_percent",))
                cofins_percent = document._nfse10_weighted_percent(("cofins_percent",))
            rec.nfse10_CST = cst if cst in valid_cst else "00"
            rec.nfse10_vBCPisCofins = _nfse10_amount(base)
            rec.nfse10_pAliqPis = f"{pis_percent:.2f}" if pis_percent else False
            rec.nfse10_pAliqCofins = (
                f"{cofins_percent:.2f}" if cofins_percent else False
            )
            rec.nfse10_vPis = _nfse10_amount(pis)
            rec.nfse10_vCofins = _nfse10_amount(cofins)
            rec.nfse10_tpRetPisCofins = "1" if withheld else "2"

    @api.depends(
        "company_id.tax_framework",
        "company_id.simplified_tax_range_id.total_tax_percent",
        "pis_percent",
        "cofins_percent",
        "irpj_percent",
        "csll_percent",
        "inss_percent",
        "issqn_percent",
        "document_id.nfse_nacional_concat_lines",
        "document_id.fiscal_line_ids.pis_percent",
        "document_id.fiscal_line_ids.cofins_percent",
        "document_id.fiscal_line_ids.irpj_percent",
        "document_id.fiscal_line_ids.csll_percent",
        "document_id.fiscal_line_ids.inss_percent",
        "document_id.fiscal_line_ids.issqn_percent",
        "document_id.fiscal_line_ids.price_gross",
    )
    def _compute_nfse10_tot_trib(self):
        # totTrib is a mandatory xs:choice among vTotTrib, pTotTrib, indTotTrib
        # and pTotTribSN. The national environment refuses indTotTrib and
        # pTotTribSN for a company outside the Simples Nacional (E0713), which
        # informs the approximate burden in pTotTrib instead.
        federal_fields = (
            "pis_percent",
            "cofins_percent",
            "irpj_percent",
            "csll_percent",
            "inss_percent",
        )
        for rec in self:
            simples = rec.company_id.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL
            percent = (
                rec.company_id.simplified_tax_range_id.total_tax_percent
                if simples
                else 0.0
            )
            if simples:
                rec.nfse10_indTotTrib = False if percent else "0"
                rec.nfse10_pTotTribSN = f"{percent:.2f}" if percent else False
                rec.nfse10_pTotTrib = False
                rec.nfse10_pTotTribFed = False
                rec.nfse10_pTotTribEst = False
                rec.nfse10_pTotTribMun = False
                continue
            rec.nfse10_indTotTrib = False
            rec.nfse10_pTotTribSN = False
            rec.nfse10_pTotTrib = rec.id
            if rec._nfse10_declares_document():
                document = rec.document_id
                federal = document._nfse10_weighted_percent(federal_fields)
                municipal = document._nfse10_weighted_percent(("issqn_percent",))
            else:
                # The approximate federal burden of a service adds the
                # withheld IRPJ, CSLL and INSS to PIS/COFINS: leaving them out
                # understates pTotTribFed and the DANFSE approximate total.
                federal = sum(rec[field] or 0.0 for field in federal_fields)
                municipal = rec.issqn_percent or 0.0
            rec.nfse10_pTotTribFed = f"{federal:.2f}"
            rec.nfse10_pTotTribEst = "0.00"
            rec.nfse10_pTotTribMun = f"{municipal:.2f}"

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
            "nfse10_pTotTrib",
        ]
        if field_name in internal_stack_mappings:
            return self._build_binding(
                class_name=class_obj._fields[field_name].comodel_name,
                field_name=field_name,
            )
        return super()._export_many2one(field_name, xsd_required, class_obj)
