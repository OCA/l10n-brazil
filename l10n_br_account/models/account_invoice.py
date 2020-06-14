# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

INVOICE_TO_OPERATION = {
    'out_invoice': 'out',
    'in_invoice': 'in',
    'out_refund': 'in',
    'in_refund': 'out',
}

REFUND_TO_OPERATION = {
    'out_invoice': 'in',
    'in_invoice': 'out',
    'out_refund': 'out',
    'in_refund': 'in',
}

FISCAL_TYPE_REFUND = {
    'out': ['purchase_return', 'in_return'],
    'in': ['sale_return', 'out_return'],
}

SHADOWED_FIELDS = ['partner_id', 'company_id', 'date', 'currency_id']


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'
    _inherits = {'l10n_br_fiscal.document': 'fiscal_document_id'}
    _order = 'date_invoice DESC, number DESC'

    # initial account.invoice inherits on fiscal.document that are
    # disable with active=False in their fiscal_document table.
    # To make these invoices still visible, we set active=True
    # in the invoice table.
    active = fields.Boolean(
        string='Active',
        default=True)

    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        related='partner_id.cnpj_cpf')

    legal_name = fields.Char(
        string='Adapted Legal Name',
        related='partner_id.legal_name')

    ie = fields.Char(
        string='Adapted State Tax Number',
        related='partner_id.inscr_est')

    # this default should be overwritten to False in a module pretending to
    # create fiscal documents from the invoices. But this default here
    # allows to install the l10n_br_account module without creating issues
    # with the existing Odoo invoice (demo or not).
    fiscal_document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
        required=True,
        ondelete="restrict",  # or cascade?
        default=lambda self: self.env.ref(
            "l10n_br_fiscal.fiscal_document_dummy"),
    )

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
        invoice = super(AccountInvoice, self).create(values)
        if invoice.fiscal_document_id != dummy_doc:
            shadowed_fiscal_vals = invoice._prepare_shadowed_fields_dict()
            invoice.fiscal_document_id.write(shadowed_fiscal_vals)
        return invoice

    @api.multi
    def write(self, values):
        dummy_doc = self.env.ref('l10n_br_fiscal.fiscal_document_dummy')
        result = super(AccountInvoice, self).write(values)
        for invoice in self:
            if invoice.fiscal_document_id != dummy_doc:
                shadowed_fiscal_vals = invoice._prepare_shadowed_fields_dict()
                invoice.fiscal_document_id.write(shadowed_fiscal_vals)
        return result
