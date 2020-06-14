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
                'l10n_br_fiscal.document.line.mixin.methods']
    _inherits = {'l10n_br_fiscal.document.line': 'fiscal_document_line_id'}

    # initial account.invoice.line inherits on fiscal.document.line that are
    # disable with active=False in their fiscal_document_line table.
    # To make these invoice lines still visible, we set active=True
    # in the invoice.line table.
    active = fields.Boolean(
        string='Active',
        default=True)

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
            'l10n_br_fiscal.fiscal_document_line_dummy'))

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

    @api.multi
    def write(self, vals):
        dummy_doc_line = self.env.ref(
            'l10n_br_fiscal.fiscal_document_line_dummy')
        res = super(AccountInvoiceLine, self).write(vals)
        for line in self:
            if line.fiscal_document_line_id != dummy_doc_line:
                shadowed_fiscal_vals = line._prepare_shadowed_fields_dict()
                line.fiscal_document_line_id.write(shadowed_fiscal_vals)
        return res

    @api.model
    def create(self, vals):
        dummy_doc = self.env.ref('l10n_br_fiscal.fiscal_document_dummy')
        if self.env['account.invoice'].browse(
                vals['invoice_id']).fiscal_document_id != dummy_doc:
            vals['fiscal_document_line_id'] = False
        line = super(AccountInvoiceLine, self).create(vals)
        if line.invoice_id.fiscal_document_id != dummy_doc:
            shadowed_fiscal_vals = line._prepare_shadowed_fields_dict()
            doc_id = line.invoice_id.fiscal_document_id.id
            shadowed_fiscal_vals['document_id'] = doc_id
            line.fiscal_document_line_id.write(shadowed_fiscal_vals)
        return line
