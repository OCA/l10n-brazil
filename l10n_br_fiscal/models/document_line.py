# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class DocumentLine(models.Model):
    _name = "l10n_br_fiscal.document.line"
    _inherit = "l10n_br_fiscal.document.line.abstract"
    _description = "Fiscal Document Line"

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document", string="Document"
    )
