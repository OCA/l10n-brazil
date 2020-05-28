# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..constants.fiscal import TAX_FRAMEWORK


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
                record.amount_total
                # - Valor Rentenções
            )

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

    document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        string='Document',
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        related='document_id.company_id',
        store=True,
        string='Company',
    )

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related='company_id.tax_framework',
        string='Tax Framework',
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

    additional_data = fields.Text(
        string='Additional Data',
    )

    # Amount Fields
    amount_estimate_tax = fields.Monetary(
        string='Amount Estimate Total',
        compute='_compute_amount',
        default=0.00,
    )

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

    def _document_comment_vals(self):
        return {
            'user': self.env.user,
            'ctx': self._context,
            'doc': self.document_id,
            'item': self,
        }

    def document_comment(self):
        for record in self.filtered('comment_ids'):
            record.additional_data = \
                record.additional_data and record.additional_data + ' - ' or ''
            record.additional_data += record.comment_ids.compute_message(
                record._document_comment_vals())

    @api.onchange('fiscal_operation_line_id')
    def _onchange_fiscal_operation_line_id(self):
        super(DocumentLine, self)._onchange_fiscal_operation_line_id()
        for comment_id in self.fiscal_operation_line_id.comment_ids:
            self.comment_ids += comment_id
