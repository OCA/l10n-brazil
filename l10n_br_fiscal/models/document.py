# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class Document(models.Model):
    _name = "l10n_br_fiscal.document"
    _inherit = "l10n_br_fiscal.document.abstract"
    _description = "Fiscal Document"

    # Pequeno hack, temporário, pois não devemos sobrescrever o
    # estado da invoice e do sale.
    state = fields.Selection(related="state_edoc")
    line_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.line",
        inverse_name="document_id",
        string="Document Lines",
    )
