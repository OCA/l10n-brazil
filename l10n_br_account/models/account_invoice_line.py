# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

# These fields that have the same name in account.invoice.line
# and l10n_br_fiscal.document.line.mixin. So they won't be updated
# by the _inherits system. An alternative would be changing their name
# in l10n_br_fiscal but that would make the code unreadable and fiscal mixin
# methods would fail to do what we expect from them in the Odoo objects
# where they are injected.
SHADOWED_FIELDS = ['name', 'partner_id', 'company_id', 'currency_id',
                   'product_id', 'uom_id', 'quantity', 'price_unit',
                   'discount_value']


class AccountInvoiceLine(models.Model):
    _name = 'account.move.line'
    _inherit = ['account.move.line',
                'l10n_br_fiscal.document.line.mixin.methods',
                'l10n_br_account.document.line.mixin']
    _inherits = {'l10n_br_fiscal.document.line': 'fiscal_document_line_id'}

    # initial account.invoice.line inherits on fiscal.document.line that are
    # disable with active=False in their fiscal_document_line table.
    # To make these invoice lines still visible, we set active=True
    # in the invoice.line table.
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    # this default should be overwritten to False in a module pretending to
    # create fiscal documents from the invoices. But this default here
    # allows to install the l10n_br_account module without creating issues
    # with the existing Odoo invoice (demo or not).
    fiscal_document_line_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.line',
        string='Fiscal Document Line',
        required=True,
        ondelete='cascade',
        default=lambda self: self.env.ref(
            'l10n_br_fiscal.fiscal_document_line_dummy'),
    )

    @api.depends(
        'price_unit',
        'discount',
        'invoice_line_tax_ids',
        'quantity',
        'product_id',
        'invoice_id.partner_id',
        'invoice_id.currency_id',
        'invoice_id.company_id',
        # 'invoice_id.date_invoice', # TODO MIGRATION 14
        'invoice_id.date',
        'fiscal_tax_ids')
    def _compute_price(self):
        for record in self:
            currency = record.invoice_id and record.invoice_id.currency_id or None
            taxes = {}
            if record.invoice_line_tax_ids:
                taxes = record.invoice_line_tax_ids.compute_all(
                    price_unit=record.price_unit,
                    currency=record.invoice_id.currency_id,
                    quantity=record.quantity,
                    product=record.product_id,
                    partner=record.invoice_id.partner_id,
                    fiscal_taxes=record.fiscal_tax_ids,
                    operation_line=record.fiscal_operation_line_id,
                    ncm=record.ncm_id,
                    nbm=record.nbm_id,
                    cest=record.cest_id,
                    discount_value=record.discount_value,
                    insurance_value=record.insurance_value,
                    other_costs_value=record.other_costs_value,
                    freight_value=record.freight_value,
                    fiscal_price=record.fiscal_price,
                    fiscal_quantity=record.fiscal_quantity,
                    uot=record.uot_id,
                    icmssn_range=record.icmssn_range_id)

            if taxes:
                record.price_subtotal = taxes['total_excluded']
                record.price_total = taxes['total_included']
            else:
                record.price_subtotal = record.quantity * record.price_unit
                record.price_total = record.price_subtotal

            record.price_subtotal -= record.discount_value
            price_subtotal_signed = record.price_subtotal

            record.price_total += (
                record.insurance_value + record.other_costs_value +
                record.freight_value - record.discount_value)

            if (record.invoice_id.currency_id and record.invoice_id.currency_id
                    != record.invoice_id.company_id.currency_id):
                currency = record.invoice_id.currency_id
                date = record.invoice_id._get_currency_rate_date()
                price_subtotal_signed = currency._convert(
                    price_subtotal_signed, record.invoice_id.company_id.currency_id,
                    record.company_id or record.env.user.company_id,
                    date or fields.Date.today())
            sign = record.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
            record.price_subtotal_signed = price_subtotal_signed * sign

    @api.depends('price_total')
    def _get_price_tax(self):
        for l in self:
            l.price_tax = l.price_total - l.price_subtotal

    @api.model
    def _shadowed_fields(self):
        """Returns the list of shadowed fields that are synced
        from the parent."""
        return SHADOWED_FIELDS


    def _prepare_shadowed_fields_dict(self, default=False):
        self.ensure_one()
        vals = self._convert_to_write(self.read(self._shadowed_fields())[0])
        if default:  # in case you want to use new rather than write later
            return {"default_%s" % (k,): vals[k] for k in vals.keys()}
        return vals

    @api.model
    def create(self, values):
        dummy_doc = self.env.ref('l10n_br_fiscal.fiscal_document_dummy')
        if self.env['account.move'].browse(
                values['invoice_id']).fiscal_document_id != dummy_doc:
            values['fiscal_document_line_id'] = False
        line = super().create(values)
        if line.invoice_id.fiscal_document_id != dummy_doc:
            shadowed_fiscal_vals = line._prepare_shadowed_fields_dict()
            doc_id = line.invoice_id.fiscal_document_id.id
            shadowed_fiscal_vals['document_id'] = doc_id
            line.fiscal_document_line_id.write(shadowed_fiscal_vals)
        return line


    def write(self, values):
        dummy_doc_line = self.env.ref(
            'l10n_br_fiscal.fiscal_document_line_dummy')
        result = super().write(values)
        for line in self:
            if line.fiscal_document_line_id != dummy_doc_line:
                shadowed_fiscal_vals = line._prepare_shadowed_fields_dict()
                line.fiscal_document_line_id.write(shadowed_fiscal_vals)
        return result
