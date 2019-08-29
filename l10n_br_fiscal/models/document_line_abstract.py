# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from ..constants.fiscal import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_SERVICE,
    FISCAL_IN_OUT,
    FISCAL_IN,
    FISCAL_OUT,
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
    def _get_default_ncm_id(self):
        fiscal_type = self.env.context.get('default_fiscal_type')
        if fiscal_type == PRODUCT_FISCAL_TYPE_SERVICE:
            ncm_id = self.env.ref(NCM_FOR_SERVICE_REF)
            return ncm_id

    document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.abstract',
        string='Document')

    operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Operation')

    operation_line_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation.line',
        string='Operation Line')

    operation_type = fields.Selection(
        selection=FISCAL_IN_OUT,
        related='operation_id.operation_type',
        string='Operation Type',
        readonly=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        related='document_id.company_id',
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
        string='CFOP')

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')

    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='UOM')

    quantity = fields.Float(
        string='Quantity')

    price = fields.Monetary(
        string='Price Unit')

    fiscal_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Fiscal UOM')

    fiscal_quantity = fields.Float(
        string='Fiscal Quantity')

    fiscal_price = fields.Monetary(
        string='Fiscal Price')

    discount = fields.Monetary(
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
        string='IPI Guideline')

    # PIS/COFINS Fields


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

    @api.onchange('product_id', 'operation_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            # Fiscal UOM self.fiscal_uom_id = self.ncm_id.uom_id
            self.ncm_id = self.product_id.ncm_id
            self.cest_id = self.product_id.cest_id
            self.nbs_id = self.product_id.nbs_id

        operation = self.operation_id or self.document_id.operation_id

        if operation:
            self.operation_line_id = self.operation_id.line_definition(
                company=self.document_id.company_id,
                partner=self.document_id.partner_id,
                item=self.product_id)

            if self.operation_line_id:
                self.cfop_id = self.operation_line_id.cfop_id

    @api.onchange('uom_id', 'price', 'quantity')
    def _onchange_commercial_quantity(self):
        if self.uom_id:
            self.fiscal_uom_id = self.uom_id

        if self.price:
            self.fiscal_price = self.price

        if self.quantity:
            self.fiscal_quantity = self.quantity

    @api.onchange('ncm_id')
    def _onchange_ncm_id(self):
        self._set_ipi()
        self._set_ii()

    @api.onchange('ipi_tax_id', 'ipi_base', 'ipi_percent',
                  'ipi_reduction', 'ipi_value')
    def _onchange_ipi_fields(self):
        if self.ipi_tax_id:
            self.ipi_tax_id.compute_taxes(
                self.company_id, self.partner_id, self.product_id)
        else:
            pass

    @api.multi
    def _set_ipi(self):
        for line in self:
            if line.cfop_id.tribute_ipi:
                if line.ncm_id:
                    line.ipi_tax_id = line.ncm_id.tax_ipi_id
            else:
                line.ipi_tax_id = False
                line.ipi_cst_id = False

            if line.ipi_tax_id:
                if line.operation_type == FISCAL_IN:
                    line.ipi_cst_id = line.ipi_tax_id.cst_in_id
                else:
                    line.ipi_cst_id = line.ipi_tax_id.cst_out_id
    @api.multi
    def _set_ii(self):
        pass

    def _compute_icms(self):
        pass
