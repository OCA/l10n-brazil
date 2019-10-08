# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class FiscalInvoiceLine(models.Model):
    _inherit = 'l10n_br_fiscal.document.line'

    # the following fields collide with account.invoice.line fields so we use
    # related field alias to be able to write them through account.invoice.line
    fiscal_doc_line_name = fields.Text(
        related='name', readonly=False)
    fiscal_doc_line_partner_id = fields.Many2one(
        related='partner_id', readonly=False)
    fiscal_doc_line_company_id = fields.Many2one(
        related='company_id', readonly=False)
    fiscal_doc_line_currency_id = fields.Many2one(
        related='currency_id', readonly=False)
    fiscal_doc_line_product_id = fields.Many2one(
        related='product_id', readonly=False)
    fiscal_doc_line_uom_id = fields.Many2one(
        related='uom_id', readonly=False)
    fiscal_doc_line_quantity = fields.Float(
        related='quantity', readonly=False)
    fiscal_doc_line_price = fields.Float(
        related='price', readonly=False)
    fiscal_doc_line_discount = fields.Float(
        related='discount', readonly=False)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
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
        default=lambda self: self.env.ref(
            'l10n_br_account.fiscal_document_line_dummy'))
