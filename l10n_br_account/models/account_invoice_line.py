# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountInvoiceLine(models.Model):
    _name = "account.invoice.line"
    _inherit = ["account.invoice.line", "l10n_br_fiscal.document.line.mixin"]
    _inherits = {"l10n_br_fiscal.document.line": "fiscal_document_line_id"}

    # initial account.invoice.line inherits on fiscal.document.line that are
    # disable with active=False in their fiscal_document_line table.
    # To make these invoice lines still visible, we set active=True
    # in the invoice.line table.
    active = fields.Boolean(
        string="Active",
        default=True)

    # this default should be overwritten to False in a module pretending to
    # create fiscal documents from the invoices. But this default here
    # allows to install the l10n_br_account module without creating issues
    # with the existing Odoo invoice (demo or not).
    fiscal_document_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.line",
        string="Fiscal Document Line",
        required=True,
        ondelete="cascade",
        default=lambda self: self.env.ref(
            "l10n_br_fiscal.fiscal_document_line_dummy"))
