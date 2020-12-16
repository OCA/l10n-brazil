# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..constants.fiscal import (TAX_FRAMEWORK)


class DocumentLine(models.Model):
    _name = 'l10n_br_fiscal.document.line'
    _inherit = 'l10n_br_fiscal.document.line.mixin'
    _description = 'Fiscal Document Line'

    @api.depends(
        'fiscal_price',
        'discount_value',
        'insurance_value',
        'other_costs_value',
        'freight_value',
        'fiscal_quantity',
        'amount_tax_not_included',
        'uot_id',
        'product_id',
        'document_id.partner_id',
        'document_id.company_id')
    def _compute_amount(self):
        for record in self:
            round_curr = record.document_id.currency_id.round
            # Valor dos produtos
            record.amount_untaxed = round_curr(record.price_unit *
                                               record.quantity)
            record.amount_fiscal = round_curr(
                record.fiscal_price * record.fiscal_quantity)

            amount_insurance_other_freight_discount = (
                record.insurance_value +
                record.other_costs_value +
                record.freight_value -
                record.discount_value -
                record.icms_relief_value
            )

            record.amount_operation = (
                record.amount_untaxed +
                amount_insurance_other_freight_discount
            )
            record.amount_fiscal_operation = (
                record.amount_fiscal +
                amount_insurance_other_freight_discount
                # + Impostos de importação
            )

            record.amount_tax = record.amount_tax_not_included
            # Valor do documento (NF)
            record.amount_total = (
                record.amount_untaxed +
                record.amount_tax +
                amount_insurance_other_freight_discount
            )

            record.amount_financial = (
                record.amount_total -
                record.amount_tax_withholding
            )

    @api.depends('fiscal_operation_type')
    def _compute_tax_framework(self):
        for record in self:
            if record.fiscal_operation_type == 'out':
                record.tax_framework = record.company_id.tax_framework
            elif record.fiscal_operation_type == 'in':
                record.tax_framework = record.partner_id.tax_framework

    @api.depends(
        'exclude_icms',
        'exclude_icms_st',
        'exclude_ipi',
        'exclude_insurance',
        'exclude_pis',
        'exclude_cofins',
        'exclude_freight',
        'exclude_other_costs',
        'amount_total')
    def _compute_amount_total_cost(self):
        for record in self:
            record.amount_total_cost = record.amount_total

            if record.exclude_icms:
                record.amount_total_cost -= record.icms_value
            if record.exclude_icms_st:
                record.amount_total_cost -= record.icmsst_value
            if record.exclude_ipi:
                record.amount_total_cost -= record.ipi_value
            if record.exclude_insurance:
                record.amount_total_cost -= record.insurance_value
            if record.exclude_pis:
                record.amount_total_cost -= record.pis_value
            if record.exclude_cofins:
                record.amount_total_cost -= record.cofins_value
            if record.exclude_freight:
                record.amount_total_cost -= record.freight_value
            if record.exclude_other_costs:
                record.amount_total_cost -= record.other_costs_value

            record.amount_total_cost /= record.quantity

    @api.model
    def _operation_domain(self):
        domain = [('state', '=', 'approved')]
        return domain

    fiscal_operation_id = fields.Many2one(
        domain=lambda self: self._operation_domain(),
    )

    document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        string='Document',
    )

    # used mostly to enable _inherits of account.invoice on fiscal_document
    # when existing invoices have no fiscal document.
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    name = fields.Text(
        string='Name',
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        related='document_id.company_id',
        store=True,
        string='Company',
    )

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        string='Tax Framework',
        compute='_compute_tax_framework',
    )

    partner_id = fields.Many2one(
        related='document_id.partner_id',
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        string='Currency',
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )

    # Amount Fields
    amount_untaxed = fields.Monetary(
        string='Amount Untaxed',
        compute='_compute_amount',
        default=0.00,
    )

    amount_tax = fields.Monetary(
        string='Amount Tax',
        compute='_compute_amount',
        default=0.00,
    )

    amount_fiscal = fields.Monetary(
        string='Amount Fiscal',
        compute='_compute_amount',
        default=0.00,
    )

    amount_operation = fields.Monetary(
        string='Amount Operation',
        compute='_compute_amount',
        default=0.00,
    )

    amount_fiscal_operation = fields.Monetary(
        string='Amount Fiscal Operation',
        compute='_compute_amount',
        default=0.00,
    )

    amount_financial = fields.Monetary(
        string='Amount Financial',
        compute='_compute_amount',
        default=0.00,
    )

    amount_total = fields.Monetary(
        string='Amount Total',
        compute='_compute_amount',
        default=0.00,
    )

    # Entry fields
    product_name = fields.Char(
        string='Vendor Product Name',
    )
    product_code = fields.Char(
        string='Vendor Product Code',
    )
    qty_received = fields.Float(
        string='Received',
    )
    entry_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit",
    )
    entry_cfop_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cfop',
        string='In CFOP',
    )

    # CMC
    exclude_icms = fields.Boolean(
        string='Exclude ICMS'
    )
    exclude_icms_st = fields.Boolean(
        string='Exclude ICMS ST'
    )
    exclude_ipi = fields.Boolean(
        string='Exclude IPI'
    )
    exclude_insurance = fields.Boolean(
        string='Exclude Insurance'
    )
    exclude_pis = fields.Boolean(
        string='Exclude PIS'
    )
    exclude_cofins = fields.Boolean(
        string='Exclude COFINS'
    )
    exclude_freight = fields.Boolean(
        string='Exclude Freight'
    )
    exclude_other_costs = fields.Boolean(
        string='Exclude Other Costs'
    )
    amount_total_cost = fields.Monetary(
        string='Entry Cost',
        compute='_compute_amount_total_cost',
        default=0.00,
    )
