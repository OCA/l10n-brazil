# Copyright (C) 2021 - TODAY Gabriel Cardoso de Faria - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    invoice_line_ids = fields.One2many(
        comodel_name="account.invoice.line",
        inverse_name="fiscal_document_line_id",
        string="Invoice Lines",
    )
