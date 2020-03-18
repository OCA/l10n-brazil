# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

# from lxml import etree
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

from ..constants.fiscal import (
    FISCAL_IN_OUT,
    TAX_FRAMEWORK_SIMPLES_ALL,
    CFOP_DESTINATION,
    NCM_FOR_SERVICE_REF,
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_SERVICE,
    TAX_BASE_TYPE,
    TAX_BASE_TYPE_PERCENT,
    TAX_DOMAIN_ISSQN,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ICMS_SN,
    TAX_DOMAIN_ICMS_ST,
    TAX_DOMAIN_ICMS_FCP,
    TAX_DOMAIN_IPI,
    TAX_DOMAIN_II,
    TAX_DOMAIN_PIS,
    TAX_DOMAIN_PIS_ST,
    TAX_DOMAIN_COFINS,
    TAX_DOMAIN_COFINS_ST
)

from ..constants.icms import (
    ICMS_ORIGIN,
    ICMS_ORIGIN_DEFAULT,
    ICMS_BASE_TYPE,
    ICMS_BASE_TYPE_DEFAULT,
    ICMS_ST_BASE_TYPE,
    ICMS_ST_BASE_TYPE_DEFAULT
)

from .tax import TAX_DICT_VALUES


FISCAL_TAX_ID_FIELDS = [
    'issqn_tax_id',
    'icms_tax_id',
    'icmsst_tax_id',
    'icmsfcp_tax_id',
    'icmssn_tax_id',
    'ipi_tax_id',
    'ii_tax_id',
    'pis_tax_id',
    'pisst_tax_id',
    'cofins_tax_id',
    'cofinsst_tax_id'
]


FISCAL_CST_ID_FIELDS = [
    'icms_cst_id',
    'ipi_cst_id',
    'pis_cst_id',
    'pisst_cst_id',
    'cofins_cst_id',
    'cofinsst_cst_id'
]


class DocumentFiscalLineMixin(models.AbstractModel):
    _name = "l10n_br_fiscal.document.line.mixin"
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
    def _get_default_ncm_id(self):
        fiscal_type = self.env.context.get("default_fiscal_type")
        if fiscal_type == PRODUCT_FISCAL_TYPE_SERVICE:
            ncm_id = self.env.ref(NCM_FOR_SERVICE_REF)
            return ncm_id

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

    price_unit = fields.Float(
        string="Price Unit",
        digits=dp.get_precision("Product Price"))

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
        default=_get_default_ncm_id,
        string="NCM")

    cest_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cest",
        index=True,
        string="CEST",
        domain="[('ncm_ids', '=', ncm_id)]")

    nbs_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.nbs",
        index=True,
        string="NBS")

    operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Operation",
        domain=lambda self: self._operation_domain(),
        default=_default_operation)

    operation_type = fields.Selection(
        selection=FISCAL_IN_OUT,
        related="operation_id.operation_type",
        string="Operation Type",
        readonly=True)

    operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line",
        domain="[('operation_id', '=', operation_id), "
               "('state', '=', 'approved')]")

    cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP",
        domain="[('type_in_out', '=', operation_type)]")

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

    discount_value = fields.Monetary(
        string="Discount Value",
        default=0.00)

    insurance_value = fields.Monetary(
        string='Insurance Value',
        default=0.00)

    other_costs_value = fields.Monetary(
        string='Other Costs',
        default=0.00)

    freight_value = fields.Monetary(
        string='Freight Value',
        default=0.00)

    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='fiscal_tax_rel',
        column1='document_id',
        column2='fiscal_tax_id',
        string="Fiscal Taxes")

    amount_tax_not_included = fields.Monetary(
        string="Amount Tax not Included",
        default=0.00)

    fiscal_genre_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.product.genre",
        string="Fiscal Genre")

    fiscal_genre_code = fields.Char(
        related="fiscal_genre_id.code",
        string="Product Genre Code")

    service_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.service.type",
        string="Service Type",
        domain="[('internal_type', '=', 'normal')]")

    # ISSQN Fields
    issqn_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ISSQN",
        domain=[('tax_domain', '=', TAX_DOMAIN_ISSQN)])

    issqn_base = fields.Monetary(
        string="ISSQN Base",
        default=0.00)

    issqn_percent = fields.Float(
        string="ISSQN %",
        default=0.00)

    issqn_reduction = fields.Float(
        string="ISSQN % Reduction",
        default=0.00)

    issqn_value = fields.Monetary(
        string="ISSQN Value",
        default=0.00)

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

    icms_base = fields.Monetary(
        string="ICMS Base",
        default=0.00)

    icms_percent = fields.Float(
        string="ICMS %",
        default=0.00)

    icms_reduction = fields.Float(
        string="ICMS % Reduction",
        default=0.00)

    icms_value = fields.Monetary(
        string="ICMS Value",
        default=0.00)

    # motDesICMS - Motivo da desoneração do ICMS
    icms_relief_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.icms.relief",
        string="ICMS Relief")

    # vICMSDeson - Valor do ICMS desonerado
    icms_relief_value = fields.Monetary(
        string="ICMS Relief Value",
        default=0.00)

    # ICMS ST Fields
    icmsst_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS ST",
        domain=[('tax_domain', '=', TAX_DOMAIN_ICMS_ST)])

    # modBCST - Modalidade de determinação da BC do ICMS ST
    icmsst_base_type = fields.Selection(
        selection=ICMS_ST_BASE_TYPE,
        string="ICMS ST Base Type",
        required=True,
        default=ICMS_ST_BASE_TYPE_DEFAULT)

    # pMVAST - Percentual da margem de valor Adicionado do ICMS ST
    icmsst_mva_percent = fields.Float(
        string="ICMS ST MVA %",
        default=0.00)

    # pRedBCST - Percentual da Redução de BC do ICMS ST
    icmsst_reduction = fields.Float(
        string="ICMS ST % Reduction",
        default=0.00)

    # vBCST - Valor da BC do ICMS ST
    icmsst_base = fields.Monetary(
        string="ICMS ST Base",
        default=0.00)

    # pICMSST - Alíquota do imposto do ICMS ST
    icmsst_percent = fields.Float(
        string="ICMS ST %",
        default=0.00)

    # vICMSST - Valor do ICMS ST
    icmsst_value = fields.Monetary(
        string="ICMS ST Value",
        default=0.00)

    icmsst_wh_base = fields.Monetary(
        string="ICMS ST WH Base",
        default=0.00)

    icmsst_wh_value = fields.Monetary(
        string="ICMS ST WH Value",
        default=0.00)

    # ICMS FCP Fields
    icmsfcp_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS FCP",
        domain=[('tax_domain', '=', TAX_DOMAIN_ICMS_FCP)])

    # pFCPUFDest - Percentual do ICMS relativo ao Fundo de
    # Combate à Pobreza (FCP) na UF de destino
    icmsfcp_percent = fields.Float(
        string="ICMS FCP %",
        default=0.00)

    # vFCPUFDest - Valor do ICMS relativo ao Fundo
    # de Combate à Pobreza (FCP) da UF de destino
    icmsfcp_value = fields.Monetary(
        string="ICMS FCP Value",
        default=0.00)

    # ICMS DIFAL Fields
    # vBCUFDest - Valor da BC do ICMS na UF de destino
    icms_destination_base = fields.Monetary(
        string="ICMS Destination Base",
        default=0.00)

    # pICMSUFDest - Alíquota interna da UF de destino
    icms_origin_percent = fields.Float(
        string="ICMS Internal %",
        default=0.00)

    # pICMSInter - Alíquota interestadual das UF envolvidas
    icms_destination_percent = fields.Float(
        string="ICMS External %",
        default=0.00)

    # pICMSInterPart - Percentual provisório de partilha do ICMS Interestadual
    icms_sharing_percent = fields.Float(
        string="ICMS Sharing %",
        default=0.00)

    # vICMSUFRemet - Valor do ICMS Interestadual para a UF do remetente
    icms_origin_value = fields.Monetary(
        string="ICMS Origin Value",
        default=0.00)

    # vICMSUFDest - Valor do ICMS Interestadual para a UF de destino
    icms_destination_value = fields.Monetary(
        string="ICMS Destination Value",
        default=0.00)

    # ICMS Simples Nacional Fields
    icmssn_range_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.simplified.tax.range",
        string="Simplified Range Tax",
        default=_default_icmssn_range_id)

    icmssn_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS SN",
        domain=[('tax_domain', '=', TAX_DOMAIN_ICMS_SN)])

    icmssn_base = fields.Monetary(
        string="ICMS SN Base",
        default=0.00)

    icmssn_reduction = fields.Monetary(
        string="ICMS SN Reduction",
        default=0.00)

    icmssn_percent = fields.Float(
        string="ICMS SN %",
        default=0.00)

    icmssn_credit_value = fields.Monetary(
        string="ICMS SN Credit",
        default=0.00)

    # IPI Fields
    ipi_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax IPI",
        domain=[('tax_domain', '=', TAX_DOMAIN_IPI)])

    ipi_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST IPI",
        domain="[('cst_type', '=', operation_type),"
               "('tax_domain', '=', 'ipi')]")

    ipi_cst_code = fields.Char(
        related="ipi_cst_id.code",
        string="IPI CST Code",
        store=True)

    ipi_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="IPI Base Type",
        default=TAX_BASE_TYPE_PERCENT)

    ipi_base = fields.Monetary(
        string="IPI Base")

    ipi_percent = fields.Float(
        string="IPI %")

    ipi_reduction = fields.Float(
        string="IPI % Reduction")

    ipi_value = fields.Monetary(
        string="IPI Value")

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
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    ii_percent = fields.Float(
        string="II %")

    ii_value = fields.Float(
        string='II Value',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    ii_iof_value = fields.Float(
        string='IOF Value',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    ii_customhouse_charges = fields.Float(
        string='Despesas Aduaneiras',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    # PIS/COFINS Fields
    # COFINS
    cofins_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax COFINS",
        domain=[('tax_domain', '=', TAX_DOMAIN_COFINS)])

    cofins_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST COFINS",
        domain="['|', ('cst_type', '=', operation_type),"
               "('cst_type', '=', 'all'),"
               "('tax_domain', '=', 'cofins')]")

    cofins_cst_code = fields.Char(
        related="cofins_cst_id.code",
        string="COFINS CST Code",
        store=True)

    cofins_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="COFINS Base Type",
        default=TAX_BASE_TYPE_PERCENT,
        required=True)

    cofins_base = fields.Monetary(
        string="COFINS Base")

    cofins_percent = fields.Float(
        string="COFINS %")

    cofins_reduction = fields.Float(
        string="COFINS % Reduction")

    cofins_value = fields.Monetary(
        string="COFINS Value")

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
        domain="['|', ('cst_type', '=', operation_type),"
               "('cst_type', '=', 'all'),"
               "('tax_domain', '=', 'cofinsst')]")

    cofinsst_cst_code = fields.Char(
        related="cofinsst_cst_id.code",
        string="COFINS ST CST Code",
        store=True)

    cofinsst_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="COFINS ST Base Type",
        default=TAX_BASE_TYPE_PERCENT,
        required=True)

    cofinsst_base = fields.Monetary(
        string="COFINS ST Base")

    cofinsst_percent = fields.Float(
        string="COFINS ST %")

    cofinsst_reduction = fields.Float(
        string="COFINS ST % Reduction")

    cofinsst_value = fields.Monetary(
        string="COFINS ST Value")

    # PIS
    pis_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax PIS",
        domain=[('tax_domain', '=', TAX_DOMAIN_PIS)])

    pis_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST PIS",
        domain="['|', ('cst_type', '=', operation_type),"
               "('cst_type', '=', 'all'),"
               "('tax_domain', '=', 'pis')]")

    pis_cst_code = fields.Char(
        related="pis_cst_id.code",
        string="PIS CST Code",
        store=True)

    pis_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="PIS Base Type",
        default=TAX_BASE_TYPE_PERCENT,
        required=True)

    pis_base = fields.Monetary(
        string="PIS Base")

    pis_percent = fields.Float(
        string="PIS %")

    pis_reduction = fields.Float(
        string="PIS % Reduction")

    pis_value = fields.Monetary(
        string="PIS Value")

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
        domain="['|', ('cst_type', '=', operation_type),"
               "('cst_type', '=', 'all'),"
               "('tax_domain', '=', 'pisst')]")

    pisst_cst_code = fields.Char(
        related="pisst_cst_id.code",
        string="PIS ST CST Code",
        store=True)

    pisst_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="PIS ST Base Type",
        default=TAX_BASE_TYPE_PERCENT,
        required=True)

    pisst_base = fields.Monetary(
        string="PIS ST Base")

    pisst_percent = fields.Float(
        string="PIS ST %")

    pisst_reduction = fields.Float(
        string="PIS ST % Reduction")

    pisst_value = fields.Monetary(
        string="PIS ST Value")

    @api.model
    def fields_view_get(
            self, view_id=None, view_type="form", toolbar=False, submenu=False):

        model_view = super(DocumentFiscalLineMixin, self).fields_view_get(
            view_id, view_type, toolbar, submenu)

        return model_view  # FIXME: Fields view get of fiscal line

        # if view_type == "form":
        #     fiscal_view = self.env.ref(
        #       "l10n_br_fiscal.document_fiscal_line_mixin_form")
        #
        #     doc = etree.fromstring(model_view.get("arch"))
        #
        #     for fiscal_node in doc.xpath("//group[@name='l10n_br_fiscal']"):
        #         sub_view_node = etree.fromstring(fiscal_view["arch"])
        #
        #         try:
        #             fiscal_node.getparent().replace(fiscal_node, sub_view_node)
        #             model_view["arch"] = etree.tostring(doc, encoding="unicode")
        #         except ValueError:
        #             return model_view
        #
        # return model_view

    def _compute_taxes(self, taxes, cst=None):
        return taxes.compute_taxes(
            company=self.company_id,
            partner=self.partner_id,
            product=self.product_id,
            price_unit=self.price_unit,
            quantity=self.quantity,
            uom_id=self.uom_id,
            fiscal_price=self.fiscal_price,
            fiscal_quantity=self.fiscal_quantity,
            uot_id=self.uot_id,
            discount_value=self.discount_value,
            insurance_value=self.insurance_value,
            other_costs_value=self.other_costs_value,
            freight_value=self.freight_value,
            ncm=self.ncm_id,
            cest=self.cest_id,
            operation_line=self.operation_line_id,
            icmssn_range=self.icmssn_range_id)

    @api.multi
    def compute_taxes(self):
        for line in self:
            computed_taxes = line._compute_taxes(line.fiscal_tax_ids)
        return computed_taxes

    @api.multi
    def _get_all_tax_id_fields(self):

        self.ensure_one()
        taxes = self.env['l10n_br_fiscal.tax']

        for fiscal_tax_field in FISCAL_TAX_ID_FIELDS:
            taxes |= self[fiscal_tax_field]

        return taxes

    @api.multi
    def _remove_all_fiscal_tax_ids(self):
        for l in self:
            l.fiscal_tax_ids = False

            for fiscal_tax_field in FISCAL_TAX_ID_FIELDS:
                l[fiscal_tax_field] = False

            self._set_fields_issqn(TAX_DICT_VALUES)
            self._set_fields_icms(TAX_DICT_VALUES)
            self._set_fields_icmssn(TAX_DICT_VALUES)
            self._set_fields_ipi(TAX_DICT_VALUES)
            self._set_fields_ii(TAX_DICT_VALUES)
            self._set_fields_pis(TAX_DICT_VALUES)
            self._set_fields_pisst(TAX_DICT_VALUES)
            self._set_fields_cofins(TAX_DICT_VALUES)
            self._set_fields_cofinsst(TAX_DICT_VALUES)

    @api.multi
    def _update_fiscal_tax_ids(self, taxes):
        for l in self:
            fiscal_taxes = l.fiscal_tax_ids.filtered(
                lambda ft: ft not in taxes)

            l.fiscal_tax_ids = fiscal_taxes + taxes

    @api.multi
    def _update_taxes(self):
        for l in self:
            computed_taxes = self._compute_taxes(l.fiscal_tax_ids)

            for tax in l.fiscal_tax_ids:

                computed_tax = computed_taxes.get(tax.tax_domain)

                if computed_tax:
                    if not computed_tax.get("tax_include"):
                        l.amount_tax_not_included = computed_tax.get(
                            "tax_value", 0.00)

                if tax.tax_domain == TAX_DOMAIN_IPI:
                    l.ipi_tax_id = tax
                    self._set_fields_ipi(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_II:
                    l.ii_tax_id = tax
                    self._set_fields_ii(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_PIS:
                    l.pis_tax_id = tax
                    self._set_fields_pis(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_PIS_ST:
                    l.pisst_tax_id = tax
                    self._set_fields_pisst(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_COFINS:
                    l.cofins_tax_id = tax
                    self._set_fields_cofins(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_COFINS_ST:
                    l.cofinsst_tax_id = tax
                    self._set_fields_cofinsst(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_ICMS:
                    l.icms_tax_id = tax
                    self._set_fields_icms(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_ICMS_SN:
                    l.icmssn_tax_id = tax
                    self._set_fields_icmssn(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_ICMS_ST:
                    l.icmsst_tax_id = tax
                    self._set_fields_icmsst(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_ICMS_FCP:
                    l.icmsfcp_tax_id = tax
                    self._set_fields_icmsfcp(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_ISSQN:
                    l.issqn_tax_id = tax
                    self._set_fields_issqn(computed_tax)

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        if self.operation_id:
            price = {
                "sale_price": self.product_id.list_price,
                "cost_price": self.product_id.standard_price,
            }

            self.price_unit = price.get(self.operation_id.default_price_unit,
                                        0.00)

            self.operation_line_id = self.operation_id.line_definition(
                company=self.company_id,
                partner=self.partner_id,
                product=self.product_id)

    @api.onchange("operation_line_id")
    def _onchange_operation_line_id(self):

        # Reset Taxes
        self._remove_all_fiscal_tax_ids()

        if self.operation_line_id:

            mapping_result = self.operation_line_id.map_fiscal_taxes(
                company=self.company_id,
                partner=self.partner_id,
                product=self.product_id,
                ncm=self.ncm_id,
                nbs=self.nbs_id,
                cest=self.cest_id)

            self.cfop_id = mapping_result['cfop']
            taxes = self.env['l10n_br_fiscal.tax']
            for tax in mapping_result['taxes'].values():
                taxes |= tax
            self.fiscal_tax_ids = taxes
            self._update_taxes()

        if not self.operation_line_id:
            self.cfop_id = False

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.uom_id = self.product_id.uom_id
            self.ncm_id = self.product_id.ncm_id
            self.cest_id = self.product_id.cest_id
            self.nbs_id = self.product_id.nbs_id
            self.fiscal_genre_id = self.product_id.fiscal_genre_id
            self.service_type_id = self.product_id.service_type_id
            self.uot_id = self.product_id.uot_id or self.product_id.uom_id
        else:
            self.name = False
            self.uom_id = False
            self.ncm_id = False
            self.cest_id = False
            self.nbs_id = False
            self.fiscal_genre_id = False
            self.service_type_id = False
            self.uot_id = False

        self._onchange_operation_id()

    def _set_fields_issqn(self, tax_dict):
        if tax_dict:
            self.issqn_base = tax_dict.get("base")
            self.issqn_percent = tax_dict.get("percent_amount")
            self.issqn_reduction = tax_dict.get("percent_reduction")
            self.issqn_value = tax_dict.get("tax_value")

    @api.onchange(
        "issqn_base",
        "issqn_percent",
        "issqn_reduction",
        "issqn_value")
    def _onchange_issqn_fields(self):
        pass

    def _set_fields_icms(self, tax_dict):
        if tax_dict:
            self.icms_cst_id = tax_dict.get("cst_id")
            self.icms_base = tax_dict.get("base")
            self.icms_percent = tax_dict.get("percent_amount")
            self.icms_reduction = tax_dict.get("percent_reduction")
            self.icms_value = tax_dict.get("tax_value")

            # TODO
            # self.icms_destination_base = tax_dict.get(
            #     "icms_destination_base")
            # self.icms_origin_percent = tax_dict.get("icms_origin_percent")
            # self.icms_destination_percent = tax_dict.get(
            #     "icms_destination_percent")
            # self.icms_sharing_percent = tax_dict.get("icms_sharing_percent")
            # self.icms_origin_value = tax_dict.get("icms_origin_value")

    @api.onchange(
        "icms_base",
        "icms_percent",
        "icms_reduction",
        "icms_value",
        "icms_destination_base",
        "icms_origin_percent",
        "icms_destination_percent",
        "icms_sharing_percent",
        "icms_origin_value")
    def _onchange_icms_fields(self):
        pass

    def _set_fields_icmssn(self, tax_dict):
        self.icms_cst_id = tax_dict.get("cst_id")
        self.icmssn_base = tax_dict.get("base")
        self.icmssn_percent = tax_dict.get("percent_amount")
        self.icmssn_reduction = tax_dict.get("percent_reduction")
        self.icmssn_credit_value = tax_dict.get("tax_value")

    @api.onchange(
        "icmssn_base",
        "icmssn_percent",
        "icmssn_reduction",
        "icmssn_credit_value")
    def _onchange_icmssn_fields(self):
        pass

    def _set_fields_icmsst(self, tax_dict):
        self.icmsst_base_type = tax_dict.get("icmsst_base_type")
        self.icmsst_mva_percent = tax_dict.get("icmsst_mva_percent")
        self.icmsst_percent = tax_dict.get("percent_amount")
        self.icmsst_reduction = tax_dict.get("percent_reduction")
        self.icmsst_base = tax_dict.get("base")
        self.icmsst_value = tax_dict.get("tax_value")

        # TODO - OTHER TAX icmsst_wh_tax_id
        # self.icmsst_wh_base
        # self.icmsst_wh_value

    @api.onchange(
        "icmsst_base_type",
        "icmsst_mva_percent",
        "icmsst_percent",
        "icmsst_reduction",
        "icmsst_base",
        "icmsst_value",
        "icmsst_wh_base",
        "icmsst_wh_value")
    def _onchange_icmsst_fields(self):
        pass

    def _set_fields_icmsfcp(self, tax_dict):
        self.icmsfcp_percent = tax_dict.get("percent_amount")
        self.icmsfcp_value = tax_dict.get("tax_value")

    @api.onchange(
        "icmsfcp_percent",
        "icmsfcp_value")
    def _onchange_icmsfcp_fields(self):
        pass

    def _set_fields_ipi(self, tax_dict):
        if tax_dict:
            self.ipi_cst_id = tax_dict.get("cst_id")
            self.ipi_base_type = tax_dict.get("base_type", False)
            self.ipi_base = tax_dict.get("base", 0.00)
            self.ipi_percent = tax_dict.get("percent_amount", 0.00)
            self.ipi_reduction = tax_dict.get("percent_reduction", 0.00)
            self.ipi_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "ipi_base",
        "ipi_percent",
        "ipi_reduction",
        "ipi_value")
    def _onchange_ipi_fields(self):
        pass

    def _set_fields_ii(self, tax_dict):
        if tax_dict:
            self.ii_base = tax_dict.get("base", 0.00)
            self.ii_percent = tax_dict.get("percent_amount", 0.00)
            self.ii_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "ii_base",
        "ii_percent",
        "ii_value")
    def _onchange_ii_fields(self):
        pass

    def _set_fields_pis(self, tax_dict):
        if tax_dict:
            self.pis_cst_id = tax_dict.get("cst_id")
            self.pis_base_type = tax_dict.get("base_type")
            self.pis_base = tax_dict.get("base", 0.00)
            self.pis_percent = tax_dict.get("percent_amount", 0.00)
            self.pis_reduction = tax_dict.get("percent_reduction", 0.00)
            self.pis_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "pis_base_type",
        "pis_base",
        "pis_percent",
        "pis_reduction",
        "pis_value")
    def _onchange_pis_fields(self):
        pass

    def _set_fields_pisst(self, tax_dict):
        if tax_dict:
            self.pisst_cst_id = tax_dict.get("cst_id")
            self.pisst_base_type = tax_dict.get("base_type")
            self.pisst_base = tax_dict.get("base", 0.00)
            self.pisst_percent = tax_dict.get("percent_amount", 0.00)
            self.pisst_reduction = tax_dict.get("percent_reduction", 0.00)
            self.pisst_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "pisst_base_type",
        "pisst_base",
        "pisst_percent",
        "pisst_reduction",
        "pisst_value")
    def _onchange_pisst_fields(self):
        pass

    def _set_fields_cofins(self, tax_dict):
        if tax_dict:
            self.cofins_cst_id = tax_dict.get("cst_id")
            self.cofins_base_type = tax_dict.get("base_type")
            self.cofins_base = tax_dict.get("base", 0.00)
            self.cofins_percent = tax_dict.get("percent_amount", 0.00)
            self.cofins_reduction = tax_dict.get("percent_reduction", 0.00)
            self.cofins_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "cofins_base_type",
        "cofins_base",
        "cofins_percent",
        "cofins_reduction",
        "cofins_value")
    def _onchange_cofins_fields(self):
        pass

    def _set_fields_cofinsst(self, tax_dict):
        if tax_dict:
            self.cofinsst_cst_id = tax_dict.get("cst_id")
            self.cofinsst_base_type = tax_dict.get("base_type")
            self.cofinsst_base = tax_dict.get("base", 0.00)
            self.cofinsst_percent = tax_dict.get("percent_amount", 0.00)
            self.cofinsst_reduction = tax_dict.get("percent_reduction", 0.00)
            self.cofinsst_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "cofinsst_base_type",
        "cofinsst_base",
        "cofinsst_percent",
        "cofinsst_reduction",
        "cofinsst_value")
    def _onchange_cofinsst_fields(self):
        pass

    @api.onchange(
        "issqn_tax_id",
        "icms_tax_id",
        "icmssn_tax_id",
        "icmsst_tax_id",
        "icmsfcp_tax_id",
        "ipi_tax_id",
        "ii_tax_id",
        "pis_tax_id",
        "pisst_tax_id",
        "cofins_tax_id",
        "cofinsst_tax_id",
        "fiscal_price",
        "fiscal_quantity",
        "discount_value",
        "insurance_value",
        "other_costs_value",
        "freight_value")
    def _onchange_fiscal_taxes(self):
        self._update_fiscal_tax_ids(self._get_all_tax_id_fields())
        self._update_taxes()

    @api.onchange("uot_id", "uom_id", "price_unit", "quantity")
    def _onchange_commercial_quantity(self):
        if not self.uot_id:
            self.uot_id = self.uom_id

        if self.uom_id == self.uot_id:
            self.fiscal_price = self.price_unit
            self.fiscal_quantity = self.quantity

        if self.uom_id != self.uot_id:
            self.fiscal_price = self.price_unit / self.product_id.uot_factor
            self.fiscal_quantity = self.quantity * self.product_id.uot_factor

    @api.onchange("ncm_id", "nbs_id", "cest_id")
    def _onchange_ncm_id(self):
        self._onchange_operation_id()
