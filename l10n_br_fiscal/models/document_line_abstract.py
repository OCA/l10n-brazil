# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

from ..constants.fiscal import (
    TAX_FRAMEWORK_NORMAL,
    TAX_FRAMEWORK_SIMPLES_ALL,
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_SERVICE,
    FISCAL_IN_OUT,
    FISCAL_IN,
    FISCAL_OUT,
    CFOP_DESTINATION_EXPORT,
    TAX_DOMAIN_IPI,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ICMS_SN,
    TAX_DOMAIN_PIS,
    TAX_DOMAIN_COFINS,
    TAX_BASE_TYPE,
    TAX_BASE_TYPE_PERCENT,
    NCM_FOR_SERVICE_REF)


class DocumentLineAbstract(models.AbstractModel):
    _name = 'l10n_br_fiscal.document.line.abstract'
    _description = 'Fiscal Document Line Abstract'

    @api.one
    @api.depends(
        'price', 'discount', 'quantity',
        'product_id', 'document_id.partner_id', 'document_id.company_id')
    def _compute_amount(self):
        round_curr = self.document_id.currency_id.round
        self.amount_untaxed = round_curr(self.price * self.quantity)
        self.amount_tax = 0.00
        self.amount_total = self.amount_untaxed + self.amount_tax

    @api.model
    def default_get(self, fields):
        defaults = super(DocumentLineAbstract, self).default_get(fields)
        if self.env.context.get('default_company_id'):
            company_id = self.env.context.get('default_company_id')
            operation_type = self.env.context.get('default_operation_type')
            taxes_dict = self._set_default_taxes(company_id, operation_type)
            defaults.update(taxes_dict)
        return defaults

    @api.model
    def _get_default_ncm_id(self):
        fiscal_type = self.env.context.get('default_fiscal_type')
        if fiscal_type == PRODUCT_FISCAL_TYPE_SERVICE:
            ncm_id = self.env.ref(NCM_FOR_SERVICE_REF)
            return ncm_id

    name = fields.Text(
        string='Name')

    # used mostly to enable _inherits of account.invoice on fiscal_document
    # when existing invoices have no fiscal document.
    active = fields.Boolean(
        string='Active',
        default=True)

    document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.abstract',
        string='Document')

    operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Operation')

    operation_line_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation.line',
        string='Operation Line',
        domain="[('operation_id', '=', operation_id)]")

    operation_type = fields.Selection(
        selection=FISCAL_IN_OUT,
        related='operation_id.operation_type',
        string='Operation Type',
        readonly=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        related='document_id.company_id',
        store=True,
        string='Company')

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='document_id.partner_id',
        string='Partner')

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        string='Currency')

    cfop_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cfop',
        string='CFOP',
        domain="[('type_in_out', '=', operation_type)]")

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')

    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='UOM')

    quantity = fields.Float(
        string='Quantity',
        digits=dp.get_precision('Product Unit of Measure'))

    price = fields.Float(
        string='Price Unit',
        digits=dp.get_precision('Product Price'))

    uot_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Tax UoM')

    fiscal_quantity = fields.Float(
        string='Fiscal Quantity',
        digits=dp.get_precision('Product Unit of Measure'))

    fiscal_price = fields.Float(
        string='Fiscal Price',
        digits=dp.get_precision('Product Price'))

    discount = fields.Float(
        string='Discount')

    fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE,
        string='Fiscal Type')

    fiscal_genre_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.product.genre',
        string='Fiscal Genre')

    ncm_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.ncm',
        index=True,
        default=_get_default_ncm_id,
        string='NCM')

    cest_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cest',
        index=True,
        string='CEST',
        domain="[('ncm_ids', '=', ncm_id)]")

    nbs_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.nbs',
        index=True,
        string='NBS')

    service_type_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.service.type',
        string='Service Type',
        domain="[('internal_type', '=', 'normal')]")

    # ICMS Fields
    icms_tax_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Tax ICMS',
        domain="[('tax_domain', '=', 'icms')]")

    icms_cst_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cst',
        string='CST ICMS',
        domain="[('cst_type', '=', operation_type),"
               "('tax_domain', '=', 'icms')]")

    icms_base = fields.Monetary(
        string='ICMS Base')

    icms_percent = fields.Float(
        string='ICMS %')

    icms_reduction = fields.Float(
        string='ICMS % Reduction')

    icms_value = fields.Monetary(
        string='ICMS Value')

    # ICMS Simples Nacional Fields
    icmssn_tax_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Tax ICMS SN',
        domain="[('tax_domain', '=', 'icmssn')]")

    icmssn_cst_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cst',
        string='CSOSN',
        domain="[('cst_type', '=', operation_type),"
               "('tax_domain', '=', 'icmssn')]")

    icmssn_credit_value = fields.Monetary(
        string='ICMS SN Credit')

    # IPI Fields
    ipi_tax_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Tax IPI',
        domain="[('tax_domain', '=', 'ipi')]")

    ipi_cst_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cst',
        string='CST IPI',
        domain="[('cst_type', '=', operation_type),"
               "('tax_domain', '=', 'ipi')]")

    ipi_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string='IPI Base Type',
        default=TAX_BASE_TYPE_PERCENT,
        required=True)

    ipi_base = fields.Monetary(
        string='IPI Base')

    ipi_percent = fields.Float(
        string='IPI %')

    ipi_reduction = fields.Float(
        string='IPI % Reduction')

    ipi_value = fields.Monetary(
        string='IPI Value')

    ipi_guideline_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax.ipi.guideline',
        string='IPI Guideline',
        domain="['|', ('cst_in_id', '=', ipi_cst_id),"
               "('cst_out_id', '=', ipi_cst_id)]")

    # PIS/COFINS Fields
    # COFINS
    cofins_tax_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Tax COFINS',
        domain="[('tax_domain', '=', 'cofins')]")

    cofins_cst_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cst',
        string='CST COFINS',
        domain="[('cst_type', '=', operation_type),"
               "('tax_domain', '=', 'cofins')]")

    cofins_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string='COFINS Base Type',
        default=TAX_BASE_TYPE_PERCENT,
        required=True)

    cofins_base = fields.Monetary(
        string='COFINS Base')

    cofins_percent = fields.Float(
        string='COFINS %')

    cofins_reduction = fields.Float(
        string='COFINS % Reduction')

    cofins_value = fields.Monetary(
        string='COFINS Value')

    cofins_base_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax.pis.cofins.base',
        string='COFINS Base')

    cofins_credit_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax.pis.cofins.credit',
        string='COFINS Credit')

    # COFINS ST
    cofinsst_tax_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Tax COFINS ST',
        domain="[('tax_domain', '=', 'cofinsst')]")

    cofinsst_cst_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cst',
        string='CST COFINS ST',
        domain="[('cst_type', '=', operation_type),"
               "('tax_domain', '=', 'cofinsst')]")

    cofinsst_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string='COFINS ST Base Type',
        default=TAX_BASE_TYPE_PERCENT,
        required=True)

    cofinsst_base = fields.Monetary(
        string='COFINS ST Base')

    cofinsst_percent = fields.Float(
        string='COFINS ST %')

    cofinsst_reduction = fields.Float(
        string='COFINS ST % Reduction')

    cofinsst_value = fields.Monetary(
        string='COFINS ST Value')

    # PIS
    pis_tax_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Tax PIS',
        domain="[('tax_domain', '=', 'pis')]")

    pis_cst_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cst',
        string='CST PIS',
        domain="[('cst_type', '=', operation_type),"
               "('tax_domain', '=', 'pis')]")

    pis_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string='PIS Base Type',
        default=TAX_BASE_TYPE_PERCENT,
        required=True)

    pis_base = fields.Monetary(
        string='PIS Base')

    pis_percent = fields.Float(
        string='PIS %')

    pis_reduction = fields.Float(
        string='PIS % Reduction')

    pis_value = fields.Monetary(
        string='PIS Value')

    pis_base_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax.pis.cofins.base',
        string='PIS Base Code')

    pis_credit_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax.pis.cofins.credit',
        string='PIS Credit')

    # PIS ST
    pisst_tax_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax',
        string='Tax PIS ST',
        domain="[('tax_domain', '=', 'pisst')]")

    pisst_cst_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cst',
        string='CST PIS ST',
        domain="[('cst_type', '=', operation_type),"
               "('tax_domain', '=', 'pisst')]")

    pisst_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string='PIS ST Base Type',
        default=TAX_BASE_TYPE_PERCENT,
        required=True)

    pisst_base = fields.Monetary(
        string='PIS ST Base')

    pisst_percent = fields.Float(
        string='PIS ST %')

    pisst_reduction = fields.Float(
        string='PIS ST % Reduction')

    pisst_value = fields.Monetary(
        string='PIS ST Value')

    # Amount Fields
    amount_untaxed = fields.Monetary(
        string='Amount Untaxed',
        compute='_compute_amount')

    amount_tax = fields.Monetary(
        string='Amount Tax',
        compute='_compute_amount')

    amount_total = fields.Monetary(
        string='Amount Total',
        compute='_compute_amount')

    def _set_default_taxes(self, company_id, operation_type=FISCAL_OUT):
        company = self.env['res.company'].browse(company_id)
        defaults = {}
        if not self.env.context.get('default_operation_type') == FISCAL_OUT:
            return defaults

        for tax_def in company.tax_definition_ids:
            # Default ICMS SN
            if tax_def.tax_group_id.tax_domain == TAX_DOMAIN_ICMS_SN:
                if company.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
                    defaults['icmssn_tax_id'] = tax_def.tax_id.id
                    defaults['icmssn_cst_id'] = tax_def.tax_id.cst_from_tax(
                        operation_type).id

            # Default ICMS
            if tax_def.tax_group_id.tax_domain == TAX_DOMAIN_ICMS:
                if company.tax_framework == TAX_FRAMEWORK_NORMAL:
                    defaults['icms_tax_id'] = tax_def.tax_id.id
                    defaults['icms_cst_id'] = tax_def.tax_id.cst_from_tax(
                        operation_type).id

            # Default IPI
            if tax_def.tax_group_id.tax_domain == TAX_DOMAIN_IPI:
                if company.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
                    defaults['ipi_tax_id'] = tax_def.tax_id.id
                    defaults['ipi_cst_id'] = tax_def.tax_id.cst_from_tax(
                        operation_type).id

            if (company.tax_framework == TAX_FRAMEWORK_NORMAL
                    and not company.ripi):
                defaults['ipi_tax_id'] = tax_def.tax_id.id
                defaults['ipi_cst_id'] = tax_def.tax_id.cst_from_tax(
                    operation_type).id

            # Default PIS/COFINS
            if tax_def.tax_group_id.tax_domain == TAX_DOMAIN_PIS:
                defaults['pis_tax_id'] = tax_def.tax_id.id
                defaults['pis_cst_id'] = tax_def.tax_id.cst_from_tax(
                    operation_type).id

            if tax_def.tax_group_id.tax_domain == TAX_DOMAIN_COFINS:
                defaults['cofins_tax_id'] = tax_def.tax_id.id
                defaults['cofins_cst_id'] = tax_def.tax_id.cst_from_tax(
                    operation_type).id

        return defaults

    def _compute_taxes(self, taxes, cst=None):
        return taxes.compute_taxes(
            company=self.company_id,
            partner=self.partner_id,
            item=self.product_id,
            prince=self.price,
            quantity=self.quantity,
            uom_id=self.uom_id,
            fiscal_price=self.fiscal_price,
            fiscal_quantity=self.fiscal_quantity,
            uot_id=self.uot_id,
            ncm=self.ncm_id,
            cest=self.cest_id,
            operation_type=self.operation_type)

    @api.multi
    def compute_taxes(self):
        for line in self:
            taxes = self.env['l10n_br_fiscal.tax']

            # Compute all taxes
            taxes |= (
                line.icms_tax_id + line.icmssn_tax_id +
                line.ipi_tax_id + line.pis_tax_id +
                line.pisst_tax_id + line.cofins_tax_id +
                line.cofinsst_tax_id)

            result_taxes = line._compute_taxes(taxes)
            # TODO populate field taxes
        return result_taxes

    @api.onchange('product_id', 'operation_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.uom_id = self.product_id.uom_id
            self.ncm_id = self.product_id.ncm_id
            self.cest_id = self.product_id.cest_id
            self.nbs_id = self.product_id.nbs_id
            self.uot_id = self.product_id.uot_id or self.product_id.uom_id

        self._onchange_operation_id()

    @api.onchange('operation_id')
    def _onchange_operation_id(self):

        if not self.operation_id:
            self.operation_id = self.document_id.operation_id

        if self.operation_id:
            price = {
                'sale_price': self.product_id.list_price,
                'cost_price': self.product_id.standard_price}

            self.price = price.get(self.operation_id.default_price_unit, 0.00)

            self.operation_line_id = self.operation_id.line_definition(
                company=self.document_id.company_id,
                partner=self.document_id.partner_id,
                item=self.product_id)

            if self.operation_line_id:
                if self.partner_id.state_id == self.company_id.state_id:
                    self.cfop_id = self.operation_line_id.cfop_internal_id
                elif self.partner_id.country_id != self.company_id.country_id:
                    self.cfop_id = self.operation_line_id.cfop_export_id
                else:
                    self.cfop_id = self.operation_line_id.cfop_external_id

            # Get and define default and operation taxes
            # self.set_default_taxes()

            self.compute_taxes()

    @api.onchange('uot_id', 'uom_id', 'price', 'quantity')
    def _onchange_commercial_quantity(self):
        if self.uom_id == self.uot_id:
            self.fiscal_price = self.price
            self.fiscal_quantity = self.quantity

        if self.uom_id != self.uot_id:  # TODO else: ?
            self.fiscal_price = (self.price / self.product_id.uot_factor)
            self.fiscal_quantity = (self.quantity * self.product_id.uot_factor)

    @api.onchange('ncm_id', 'nbs_id', 'cest_id')
    def _onchange_ncm_id(self):
        if self.ncm_id:
            # Get IPI from NCM
            if self.company_id.ripi:
                self.ipi_tax_id = self.ncm_id.tax_ipi_id

            # Get II from NCM but only comming from other country
            if (self.cfop_id.destination == CFOP_DESTINATION_EXPORT
                    and self.operation_type == FISCAL_IN):
                self.ii_tax_id = self.ncm_id.tax_ii_id

            # TODO cest_id compute ICMS ST

            # TODO nbs_id compute ISSQN

    @api.onchange('icms_tax_id')
    def _onchange_icms_tax_id(self):
        if self.icms_tax_id:
            self.icms_cst_id = self.icms_tax_id.cst_from_tax(
                self.operation_type)
            self.icms_base_type = self.icms_tax_id.tax_base_type

    @api.onchange('icms_base', 'icms_percent',
                  'icms_reduction', 'icms_value')
    def _onchange_icms_fields(self):
        pass

    @api.onchange('icmssn_tax_id')
    def _onchange_icmssn_tax_id(self):
        if self.icmssn_tax_id:
            self.icmssn_cst_id = self.icmssn_tax_id.cst_from_tax(
                self.operation_type)

    @api.onchange('icms_base', 'icms_percent',
                  'icms_reduction', 'icms_value')
    def _onchange_icmssn_fields(self):
        pass

    def _set_fields_ipi(self, tax_dict):
        if tax_dict:
            self.ipi_cst_id = self.ipi_tax_id.cst_from_tax(
                self.operation_type)
            self.ipi_base_type = tax_dict.get('base_type')
            self.ipi_base = tax_dict.get('base')
            self.ipi_percent = tax_dict.get('percent_amount')
            self.ipi_reduction = tax_dict.get('percent_reduction')
            self.ipi_value = tax_dict.get('tax_value')

    @api.onchange('ipi_tax_id')
    def _onchange_ipi_tax_id(self):
        if self.ipi_tax_id:
            result_taxes = self._compute_taxes(self.ipi_tax_id)
            self._set_fields_ipi(result_taxes.get(TAX_DOMAIN_IPI))

    @api.onchange('ipi_base', 'ipi_percent',
                  'ipi_reduction', 'ipi_value')
    def _onchange_ipi_fields(self):
        pass

    def _set_fields_pis(self, tax_dict):
        if tax_dict:
            self.pis_cst_id = self.pis_tax_id.cst_from_tax(
                self.operation_type)
            self.pis_base_type = tax_dict.get('base_type')
            self.pis_base = tax_dict.get('base')
            self.pis_percent = tax_dict.get('percent_amount')
            self.pis_reduction = tax_dict.get('percent_reduction')
            self.v_value = tax_dict.get('tax_value')

    @api.onchange('pis_tax_id')
    def _onchange_pis_tax_id(self):
        if self.pis_tax_id:
            result_taxes = self._compute_taxes(self.pis_tax_id)
            self._set_fields_pis(result_taxes.get(TAX_DOMAIN_PIS))

    @api.onchange('pis_base_type', 'pis_base',
                  'pis_percent', 'pis_reduction', 'pis_value')
    def _onchange_pis_fields(self):
        pass

    @api.onchange('pisst_tax_id')
    def _onchange_pisst_tax_id(self):
        if self.pisst_tax_id:
            self.pisst_cst_id = self.pisst_tax_id.cst_from_tax(
                self.operation_type)
            self.pisst_base_type = self.pisst_tax_id.tax_base_type
            # pisst = self._compute_taxes(
            #     self.pisst_tax_id,
            #     self.pisst_cst_id).get(TAX_DOMAIN_PIS_ST)

    @api.onchange('pisst_base')
    def _onchange_pisst_fields(self):
        pass

    def _set_fields_cofins(self, tax_dict):
        if tax_dict:
            self.cofins_cst_id = self.cofins_tax_id.cst_from_tax(
                self.operation_type)
            self.cofins_base_type = tax_dict.get('base_type')
            self.cofins_base = tax_dict.get('base')
            self.cofins_percent = tax_dict.get('percent_amount')
            self.cofins_reduction = tax_dict.get('percent_reduction')
            self.cofins_value = tax_dict.get('tax_value')

    @api.onchange('cofins_tax_id')
    def _onchange_cofins_tax_id(self):
        if self.cofins_tax_id:
            result_taxes = self._compute_taxes(self.cofins_tax_id)
            self._set_fields_cofins(result_taxes.get(TAX_DOMAIN_COFINS))

    @api.onchange('cofins_base_type', 'cofins_base',
                  'cofins_percent', 'cofins_reduction',
                  'cofins_value')
    def _onchange_cofins_fields(self):
        pass

    @api.onchange('cofinsst_tax_id')
    def _onchange_cofinsst_tax_id(self):
        if self.cofinsst_tax_id:
            self.cofinsst_cst_id = self.cofinsst_tax_id.cst_from_tax(
                self.operation_type)
            self.cofinsst_base_type = self.cofinsst_tax_id.tax_base_type
            # cofinsst = self._compute_taxes(
            #     self.cofinsst_tax_id,
            #     self.cofinsst_cst_id).get(TAX_DOMAIN_COFINS_ST)

    @api.onchange('cofinsst_base')
    def _onchange_cofins_fields(self):
        pass
