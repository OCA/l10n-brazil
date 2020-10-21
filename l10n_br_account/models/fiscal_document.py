# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    # the following fields collide with account.invoice fields so we use
    # related field alias to be able to write them through account.invoice
    fiscal_doc_partner_id = fields.Many2one(
        related="partner_id",
        string="Fiscal Doc Partner",
        readonly=False)

    fiscal_doc_date = fields.Datetime(
        related="date",
        string="Fiscal Doc Date",
        readonly=False)

    fiscal_doc_company_id = fields.Many2one(
        related="company_id",
        string="Fiscal Doc Company",
        readonly=False)

    fiscal_doc_currency_id = fields.Many2one(
        related="currency_id",
        string="Fiscal Doc Currency",
        readonly=False)

    fiscal_doc_state = fields.Selection(
        related="state",
        string="Fiscal Doc State",
        readonly=False)
