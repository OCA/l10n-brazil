# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

from ..constants.fiscal import (
    CFOP_DESTINATION,
    PRODUCT_FISCAL_TYPE,
    FISCAL_IN_OUT,
    TAX_BASE_TYPE,
    TAX_BASE_TYPE_PERCENT,
    TAX_DOMAIN_COFINS,
    TAX_DOMAIN_COFINS_WH,
    TAX_DOMAIN_COFINS_ST,
    TAX_DOMAIN_CSLL,
    TAX_DOMAIN_CSLL_WH,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ICMS_FCP,
    TAX_DOMAIN_ICMS_SN,
    TAX_DOMAIN_ICMS_ST,
    TAX_DOMAIN_II,
    TAX_DOMAIN_INSS,
    TAX_DOMAIN_INSS_WH,
    TAX_DOMAIN_IPI,
    TAX_DOMAIN_IRPJ,
    TAX_DOMAIN_IRPJ_WH,
    TAX_DOMAIN_ISSQN,
    TAX_DOMAIN_ISSQN_WH,
    TAX_DOMAIN_PIS,
    TAX_DOMAIN_PIS_WH,
    TAX_DOMAIN_PIS_ST,
    TAX_FRAMEWORK_SIMPLES_ALL,
    FISCAL_COMMENT_LINE,
    TAX_ICMS_OR_ISSQN,
)

from ..constants.icms import (
    ICMS_ORIGIN,
    ICMS_ORIGIN_DEFAULT,
    ICMS_BASE_TYPE,
    ICMS_BASE_TYPE_DEFAULT,
    ICMS_ST_BASE_TYPE,
    ICMS_ST_BASE_TYPE_DEFAULT
)

from ..constants.issqn import (
    ISSQN_ELIGIBILITY,
    ISSQN_ELIGIBILITY_DEFAULT,
    ISSQN_INCENTIVE,
    ISSQN_INCENTIVE_DEFAULT,
)


class FiscalDocumentLineMixin(models.AbstractModel):
    _name = "l10n_br_fiscal.document.line.mixin"
    _inherit = "l10n_br_fiscal.document.line.mixin.methods"
    _description = "Document Fiscal Mixin"

    @api.model
    def _default_operation(self):
        return False

    @api.model
    def _default_icmssn_range_id(self):
        company = self.env.user.company_id
        stax_range_id = self.env['l10n_br_fiscal.simplified.tax.range']

        if self.env.context.get("default_company_id"):
            company = self.env['res.company'].browse(
                self.env.context.get("default_company_id"))

        if company.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
            stax_range_id = company.simplifed_tax_range_id

        return stax_range_id

    @api.model
    def _operation_domain(self):
        domain = [('state', '=', 'approved')]
        return domain

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.ref('base.BRL'))

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product")

    tax_icms_or_issqn = fields.Selection(
        selection=TAX_ICMS_OR_ISSQN,
        string='ICMS or ISSQN Tax',
        default=TAX_DOMAIN_ICMS,
    )

    price_unit = fields.Float(
        string="Price Unit",
        digits=dp.get_precision("Product Price"))

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner")

    partner_company_type = fields.Selection(
        related="partner_id.company_type")

    uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="UOM")

    quantity = fields.Float(
        string="Quantity",
        digits=dp.get_precision("Product Unit of Measure"))

    fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE,
        string="Fiscal Type")

    ncm_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.ncm",
        index=True,
        string="NCM")

    nbm_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.nbm",
        index=True,
        string="NBM",
        domain="[('ncm_ids', '=', ncm_id)]")

    cest_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cest",
        index=True,
        string="CEST",
        domain="[('ncm_ids', '=', ncm_id)]")

    nbs_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.nbs",
        index=True,
        string="NBS")

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Operation",
        domain=lambda self: self._operation_domain(),
        default=_default_operation)

    fiscal_operation_type = fields.Selection(
        selection=FISCAL_IN_OUT,
        related="fiscal_operation_id.fiscal_operation_type",
        string="Fiscal Operation Type",
        readonly=True)

    fiscal_operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line",
        domain="[('fiscal_operation_id', '=', fiscal_operation_id), "
               "('state', '=', 'approved')]")

    cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP",
        domain="[('type_in_out', '=', fiscal_operation_type)]")

    cfop_destination = fields.Selection(
        selection=CFOP_DESTINATION,
        related="cfop_id.destination",
        string="CFOP Destination")

    fiscal_price = fields.Float(
        string="Fiscal Price",
        digits=dp.get_precision("Product Price"))

    uot_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Tax UoM")

    fiscal_quantity = fields.Float(
        string="Fiscal Quantity",
        digits=dp.get_precision("Product Unit of Measure"))

    discount_value = fields.Monetary(string="Discount Value")

    insurance_value = fields.Monetary(string="Insurance Value")

    other_costs_value = fields.Monetary(string="Other Costs")

    freight_value = fields.Monetary(string="Freight Value")

    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='fiscal_tax_rel',
        column1='document_id',
        column2='fiscal_tax_id',
        string="Fiscal Taxes")

    amount_tax_not_included = fields.Monetary(string="Amount Tax not Included")

    amount_tax_withholding = fields.Monetary(string="Amount Tax Withholding")

    fiscal_genre_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.product.genre",
        string="Fiscal Product Genre")

    fiscal_genre_code = fields.Char(
        related="fiscal_genre_id.code",
        string="Fiscal Product Genre Code")

    service_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.service.type",
        string="Service Type LC 166",
        domain="[('internal_type', '=', 'normal')]")

    city_taxation_code_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.city.taxation.code',
        string='City Taxation Code')

    partner_order = fields.Char(
        string='Partner Order (xPed)',
        size=15)

    partner_order_line = fields.Char(
        string='Partner Order Line (nItemPed)',
        size=6)

    # ISSQN Fields
    issqn_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ISSQN",
        domain=[('tax_domain', '=', TAX_DOMAIN_ISSQN)])

    issqn_fg_city_id = fields.Many2one(
        comodel_name="res.city",
        string="ISSQN City",
    )

    # vDeducao
    issqn_deduction_amount = fields.Monetary(string="ISSQN Deduction Value")

    # vOutro
    issqn_other_amount = fields.Monetary(string="ISSQN Other Value")

    # vDescIncond
    issqn_desc_incond_amount = fields.Monetary(string="ISSQN Discount Incond")

    # vDescCond
    issqn_desc_cond_amount = fields.Monetary(string="ISSQN Discount Cond")

    # indISS
    issqn_eligibility = fields.Selection(
        selection=ISSQN_ELIGIBILITY,
        string='ISSQN Eligibility',
        default=ISSQN_ELIGIBILITY_DEFAULT,
    )

    # indIncentivo
    issqn_incentive = fields.Selection(
        selection=ISSQN_INCENTIVE,
        string='ISSQN Incentive',
        default=ISSQN_INCENTIVE_DEFAULT,
    )

    issqn_base = fields.Monetary(string="ISSQN Base")

    issqn_percent = fields.Float(string="ISSQN %")

    issqn_reduction = fields.Float(string="ISSQN % Reduction")

    issqn_value = fields.Monetary(string="SSQN Value")

    issqn_wh_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ISSQN RET",
        domain=[('tax_domain', '=', TAX_DOMAIN_ISSQN_WH)])

    issqn_wh_base = fields.Monetary(string="ISSQN RET Base")

    issqn_wh_percent = fields.Float(string="ISSQN RET %")

    issqn_wh_reduction = fields.Float(string="ISSQN RET % Reduction")

    issqn_wh_value = fields.Monetary(string="ISSQN RET Value")

    # ICMS Fields
    icms_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS",
        domain=[('tax_domain', '=', TAX_DOMAIN_ICMS)])

    icms_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST ICMS",
        domain="[('tax_domain', '=', {'1': 'icmssn', '2': 'icmssn', "
               "'3': 'icms'}.get(tax_framework))]")

    icms_cst_code = fields.Char(
        related="icms_cst_id.code",
        string="ICMS CST Code",
        store=True)

    icms_base_type = fields.Selection(
        selection=ICMS_BASE_TYPE,
        string="ICMS Base Type",
        default=ICMS_BASE_TYPE_DEFAULT)

    icms_origin = fields.Selection(
        selection=ICMS_ORIGIN,
        string="ICMS Origin",
        default=ICMS_ORIGIN_DEFAULT)

    icms_base = fields.Monetary(string="ICMS Base")

    icms_percent = fields.Float(string="ICMS %")

    icms_reduction = fields.Float(string="ICMS % Reduction")

    icms_value = fields.Monetary(string="ICMS Value")

    # motDesICMS - Motivo da desoneração do ICMS
    icms_relief_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.icms.relief",
        string="ICMS Relief")

    # vICMSDeson - Valor do ICMS desonerado
    icms_relief_value = fields.Monetary(string="ICMS Relief Value")

    # ICMS ST Fields
    icmsst_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS ST",
        domain=[('tax_domain', '=', TAX_DOMAIN_ICMS_ST)])

    # modBCST - Modalidade de determinação da BC do ICMS ST
    icmsst_base_type = fields.Selection(
        selection=ICMS_ST_BASE_TYPE,
        string="ICMS ST Base Type",
        default=ICMS_ST_BASE_TYPE_DEFAULT)

    # pMVAST - Percentual da margem de valor Adicionado do ICMS ST
    icmsst_mva_percent = fields.Float(string="ICMS ST MVA %")

    # pRedBCST - Percentual da Redução de BC do ICMS ST
    icmsst_reduction = fields.Float(string="ICMS ST % Reduction")

    # vBCST - Valor da BC do ICMS ST
    icmsst_base = fields.Monetary(string="ICMS ST Base")

    # pICMSST - Alíquota do imposto do ICMS ST
    icmsst_percent = fields.Float(string="ICMS ST %")

    # vICMSST - Valor do ICMS ST
    icmsst_value = fields.Monetary(string="ICMS ST Value")

    icmsst_wh_base = fields.Monetary(string="ICMS ST WH Base")

    icmsst_wh_value = fields.Monetary(string="ICMS ST WH Value")

    # ICMS FCP Fields
    icmsfcp_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS FCP",
        domain=[('tax_domain', '=', TAX_DOMAIN_ICMS_FCP)])

    # vBCFCPUFDest
    icmsfcp_base = fields.Monetary(
        string="ICMS FCP Base",
    )

    # pFCPUFDest - Percentual do ICMS relativo ao Fundo de
    # Combate à Pobreza (FCP) na UF de destino
    icmsfcp_percent = fields.Float(string="ICMS FCP %")

    # vFCPUFDest - Valor do ICMS relativo ao Fundo
    # de Combate à Pobreza (FCP) da UF de destino
    icmsfcp_value = fields.Monetary(string="ICMS FCP Value")

    # ICMS DIFAL Fields
    # vBCUFDest - Valor da BC do ICMS na UF de destino
    icms_destination_base = fields.Monetary(string="ICMS Destination Base")

    # pICMSUFDest - Alíquota interna da UF de destino
    icms_origin_percent = fields.Float(string="ICMS Internal %")

    # pICMSInter - Alíquota interestadual das UF envolvidas
    icms_destination_percent = fields.Float(string="ICMS External %")

    # pICMSInterPart - Percentual provisório de partilha do ICMS Interestadual
    icms_sharing_percent = fields.Float(string="ICMS Sharing %")

    # vICMSUFRemet - Valor do ICMS Interestadual para a UF do remetente
    icms_origin_value = fields.Monetary(string="ICMS Origin Value")

    # vICMSUFDest - Valor do ICMS Interestadual para a UF de destino
    icms_destination_value = fields.Monetary(string="ICMS Dest. Value")

    # ICMS Simples Nacional Fields
    icmssn_range_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.simplified.tax.range",
        string="Simplified Range Tax",
        default=_default_icmssn_range_id)

    icmssn_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS SN",
        domain=[('tax_domain', '=', TAX_DOMAIN_ICMS_SN)])

    icmssn_base = fields.Monetary(string="ICMS SN Base")

    icmssn_reduction = fields.Monetary(string="ICMS SN Reduction")

    icmssn_percent = fields.Float(string="ICMS SN %")

    icmssn_credit_value = fields.Monetary(string="ICMS SN Credit")

    # IPI Fields
    ipi_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax IPI",
        domain=[('tax_domain', '=', TAX_DOMAIN_IPI)])

    ipi_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST IPI",
        domain="[('cst_type', '=', fiscal_operation_type),"
               "('tax_domain', '=', 'ipi')]")

    ipi_cst_code = fields.Char(
        related="ipi_cst_id.code",
        string="IPI CST Code",
        store=True)

    ipi_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="IPI Base Type",
        default=TAX_BASE_TYPE_PERCENT)

    ipi_base = fields.Monetary(string="IPI Base")

    ipi_percent = fields.Float(string="IPI %")

    ipi_reduction = fields.Float(string="IPI % Reduction")

    ipi_value = fields.Monetary(string="IPI Value")

    ipi_guideline_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.ipi.guideline",
        string="IPI Guideline",
        domain="['|', ('cst_in_id', '=', ipi_cst_id),"
               "('cst_out_id', '=', ipi_cst_id)]")

    # II Fields
    ii_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax II",
        domain=[('tax_domain', '=', TAX_DOMAIN_II)])

    ii_base = fields.Float(
        string='II Base',
        digits=dp.get_precision('Account'))

    ii_percent = fields.Float(string="II %")

    ii_value = fields.Float(
        string='II Value',
        digits=dp.get_precision('Account'))

    ii_iof_value = fields.Float(
        string='IOF Value',
        digits=dp.get_precision('Account'))

    ii_customhouse_charges = fields.Float(
        string='Despesas Aduaneiras',
        digits=dp.get_precision('Account'))

    # PIS/COFINS Fields
    # COFINS
    cofins_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax COFINS",
        domain=[('tax_domain', '=', TAX_DOMAIN_COFINS)])

    cofins_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST COFINS",
        domain="['|', ('cst_type', '=', fiscal_operation_type),"
               "('cst_type', '=', 'all'),"
               "('tax_domain', '=', 'cofins')]")

    cofins_cst_code = fields.Char(
        related="cofins_cst_id.code",
        string="COFINS CST Code",
        store=True)

    cofins_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="COFINS Base Type",
        default=TAX_BASE_TYPE_PERCENT)

    cofins_base = fields.Monetary(string="COFINS Base")

    cofins_percent = fields.Float(string="COFINS %")

    cofins_reduction = fields.Float(string="COFINS % Reduction")

    cofins_value = fields.Monetary(string="COFINS Value")

    cofins_base_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.pis.cofins.base",
        string="COFINS Base Code")

    cofins_credit_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.pis.cofins.credit",
        string="COFINS Credit Code")

    # COFINS ST
    cofinsst_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax COFINS ST",
        domain=[('tax_domain', '=', TAX_DOMAIN_COFINS_ST)])

    cofinsst_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST COFINS ST",
        domain="['|', ('cst_type', '=', fiscal_operation_type),"
               "('cst_type', '=', 'all'),"
               "('tax_domain', '=', 'cofinsst')]")

    cofinsst_cst_code = fields.Char(
        related="cofinsst_cst_id.code",
        string="COFINS ST CST Code",
        store=True)

    cofinsst_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="COFINS ST Base Type",
        default=TAX_BASE_TYPE_PERCENT)

    cofinsst_base = fields.Monetary(string="COFINS ST Base")

    cofinsst_percent = fields.Float(string="COFINS ST %")

    cofinsst_reduction = fields.Float(string="COFINS ST % Reduction")

    cofinsst_value = fields.Monetary(string="COFINS ST Value")

    cofins_wh_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax COFINS RET",
        domain=[('tax_domain', '=', TAX_DOMAIN_COFINS_WH)])

    cofins_wh_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="COFINS WH Base Type",
        default=TAX_BASE_TYPE_PERCENT)

    cofins_wh_base = fields.Monetary(string="COFINS RET Base")

    cofins_wh_percent = fields.Float(string="COFINS RET %")

    cofins_wh_reduction = fields.Float(string="COFINS RET % Reduction")

    cofins_wh_value = fields.Monetary(string="COFINS RET Value")

    # PIS
    pis_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax PIS",
        domain=[('tax_domain', '=', TAX_DOMAIN_PIS)])

    pis_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST PIS",
        domain="['|', ('cst_type', '=', fiscal_operation_type),"
               "('cst_type', '=', 'all'),"
               "('tax_domain', '=', 'pis')]")

    pis_cst_code = fields.Char(
        related="pis_cst_id.code",
        string="PIS CST Code",
        store=True)

    pis_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="PIS Base Type",
        default=TAX_BASE_TYPE_PERCENT)

    pis_base = fields.Monetary(string="PIS Base")

    pis_percent = fields.Float(string="PIS %")

    pis_reduction = fields.Float(string="PIS % Reduction")

    pis_value = fields.Monetary(string="PIS Value")

    pis_base_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.pis.cofins.base",
        string="PIS Base Code")

    pis_credit_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.pis.cofins.credit",
        string="PIS Credit")

    # PIS ST
    pisst_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax PIS ST",
        domain=[('tax_domain', '=', TAX_DOMAIN_PIS_ST)])

    pisst_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST PIS ST",
        domain="['|', ('cst_type', '=', fiscal_operation_type),"
               "('cst_type', '=', 'all'),"
               "('tax_domain', '=', 'pisst')]")

    pisst_cst_code = fields.Char(
        related="pisst_cst_id.code",
        string="PIS ST CST Code",
        store=True)

    pisst_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="PIS ST Base Type",
        default=TAX_BASE_TYPE_PERCENT)

    pisst_base = fields.Monetary(string="PIS ST Base")

    pisst_percent = fields.Float(string="PIS ST %")

    pisst_reduction = fields.Float(string="PIS ST % Reduction")

    pisst_value = fields.Monetary(
        string="PIS ST Value")

    pis_wh_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax PIS RET",
        domain=[('tax_domain', '=', TAX_DOMAIN_PIS_WH)])

    pis_wh_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="PIS WH Base Type",
        default=TAX_BASE_TYPE_PERCENT)

    pis_wh_base = fields.Monetary(string="PIS RET Base")

    pis_wh_percent = fields.Float(string="PIS RET %")

    pis_wh_reduction = fields.Float(string="PIS RET % Reduction")

    pis_wh_value = fields.Monetary(string="PIS RET Value")

    # CSLL Fields
    csll_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax CSLL",
        domain=[('tax_domain', '=', TAX_DOMAIN_CSLL)])

    csll_base = fields.Monetary(string="CSLL Base")

    csll_percent = fields.Float(string="CSLL %")

    csll_reduction = fields.Float(string="CSLL % Reduction")

    csll_value = fields.Monetary(string="CSLL Value")

    csll_wh_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax CSLL RET",
        domain=[('tax_domain', '=', TAX_DOMAIN_CSLL_WH)])

    csll_wh_base = fields.Monetary(string="CSLL RET Base")

    csll_wh_percent = fields.Float(string="CSLL RET %")

    csll_wh_reduction = fields.Float(string="CSLL RET % Reduction")

    csll_wh_value = fields.Monetary(string="CSLL RET Value")

    irpj_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax IRPJ",
        domain=[('tax_domain', '=', TAX_DOMAIN_IRPJ)])

    irpj_base = fields.Monetary(string="IRPJ Base")

    irpj_percent = fields.Float(string="IRPJ %")

    irpj_reduction = fields.Float(string="IRPJ % Reduction")

    irpj_value = fields.Monetary(string="IRPJ Value")

    irpj_wh_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax IRPJ RET",
        domain=[('tax_domain', '=', TAX_DOMAIN_IRPJ_WH)])

    irpj_wh_base = fields.Monetary(string="RPJ RET Base")

    irpj_wh_percent = fields.Float(string="IRPJ RET %")

    irpj_wh_reduction = fields.Float(string="IRPJ RET % Reduction")

    irpj_wh_value = fields.Monetary(string="IRPJ RET Value")

    inss_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax INSS",
        domain=[('tax_domain', '=', TAX_DOMAIN_INSS)])

    inss_base = fields.Monetary(string="INSS Base")

    inss_percent = fields.Float(string="INSS %")

    inss_reduction = fields.Float(string="INSS % Reduction")

    inss_value = fields.Monetary(string="INSS Value")

    inss_wh_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax INSS RET",
        domain=[('tax_domain', '=', TAX_DOMAIN_INSS_WH)])

    inss_wh_base = fields.Monetary(string="INSS RET Base")

    inss_wh_percent = fields.Float(string="INSS RET %")

    inss_wh_reduction = fields.Float(string="INSS RET % Reduction")

    inss_wh_value = fields.Monetary(string="INSS RET Value")

    simple_value = fields.Monetary(string="National Simple Taxes")

    simple_without_icms_value = fields.Monetary(
        string="National Simple Taxes without ICMS")

    comment_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.comment',
        relation='l10n_br_fiscal_document_line_mixin_comment_rel',
        column1='document_line_mixin_id',
        column2='comment_id',
        string='Comments',
        domain=[('object', '=', FISCAL_COMMENT_LINE)],
    )

    additional_data = fields.Char(string='Additional Data')

    amount_estimate_tax = fields.Monetary(
        string='Amount Estimate Tax',
    )
