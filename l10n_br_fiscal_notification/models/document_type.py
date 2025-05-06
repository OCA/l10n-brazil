# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class DocumentType(models.Model):
    _inherit = "l10n_br_fiscal.document.type"

    document_email_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.email",
        inverse_name="document_type_id",
        string="Email Template Definition",
    )
