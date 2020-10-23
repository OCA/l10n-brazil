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
    _name = 'account.invoice.line'
    _inherit = ['account.invoice.line',
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

    @api.one
    @api.depends(
        'price_unit',
        'discount',
        'invoice_line_tax_ids',
        'quantity',
        'product_id',
        'invoice_id.partner_id',
        'invoice_id.currency_id',
        'invoice_id.company_id',
        'invoice_id.date_invoice',
        'invoice_id.date',
        'fiscal_tax_ids')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        taxes = {}
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(
                price_unit=self.price_unit,
                currency=self.invoice_id.currency_id,
                quantity=self.quantity,
                product=self.product_id,
                partner=self.invoice_id.partner_id,
                fiscal_taxes=self.fiscal_tax_ids,
                operation_line=self.fiscal_operation_line_id,
                ncm=self.ncm_id,
                nbm=self.nbm_id,
                cest=self.cest_id,
                discount_value=self.discount_value,
                insurance_value=self.insurance_value,
                other_costs_value=self.other_costs_value,
                freight_value=self.freight_value,
                fiscal_price=self.fiscal_price,
                fiscal_quantity=self.fiscal_quantity,
                uot=self.uot_id,
                icmssn_range=self.icmssn_range_id)

        if taxes:
            self.price_subtotal = taxes['total_excluded']
            self.price_total = taxes['total_included']
        else:
            self.price_subtotal = self.quantity * self.price_unit
            self.price_total = self.price_subtotal

        self.price_subtotal -= self.discount_value
        price_subtotal_signed = self.price_subtotal

        self.price_total += (
            self.insurance_value + self.other_costs_value +
            self.freight_value - self.discount_value)

        if (self.invoice_id.currency_id and self.invoice_id.currency_id
                != self.invoice_id.company_id.currency_id):
            currency = self.invoice_id.currency_id
            date = self.invoice_id._get_currency_rate_date()
            price_subtotal_signed = currency._convert(
                price_subtotal_signed, self.invoice_id.company_id.currency_id,
                self.company_id or self.env.user.company_id,
                date or fields.Date.today())
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign

    @api.depends('price_total')
    def _get_price_tax(self):
        for l in self:
            l.price_tax = l.price_total - l.price_subtotal

    @api.model
    def _shadowed_fields(self):
        """Returns the list of shadowed fields that are synced
        from the parent."""
        return SHADOWED_FIELDS

    @api.multi
    def _prepare_shadowed_fields_dict(self, default=False):
        self.ensure_one()
        vals = self._convert_to_write(self.read(self._shadowed_fields())[0])
        if default:  # in case you want to use new rather than write later
            return {"default_%s" % (k,): vals[k] for k in vals.keys()}
        return vals

    @api.model
    def create(self, values):
        dummy_doc = self.env.ref('l10n_br_fiscal.fiscal_document_dummy')
        if self.env['account.invoice'].browse(
                values['invoice_id']).fiscal_document_id != dummy_doc:
            values['fiscal_document_line_id'] = False
        line = super().create(values)
        if line.invoice_id.fiscal_document_id != dummy_doc:
            shadowed_fiscal_vals = line._prepare_shadowed_fields_dict()
            doc_id = line.invoice_id.fiscal_document_id.id
            shadowed_fiscal_vals['document_id'] = doc_id
            line.fiscal_document_line_id.write(shadowed_fiscal_vals)
        return line

    @api.multi
    def write(self, values):
        dummy_doc_line = self.env.ref(
            'l10n_br_fiscal.fiscal_document_line_dummy')
        if values.get('invoice_id'):
            values['document_id'] = self.env[
                "account.invoice"].browse(values['invoice_id']).fiscal_document_id.id
        result = super().write(values)
        for line in self:
            if line.fiscal_document_line_id != dummy_doc_line:
                shadowed_fiscal_vals = line._prepare_shadowed_fields_dict()
                line.fiscal_document_line_id.write(shadowed_fiscal_vals)
        return result
