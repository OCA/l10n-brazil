# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

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
            "l10n_br_fiscal.fiscal_document_dummy"))
