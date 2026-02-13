# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    document_email_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.email",
        inverse_name="company_id",
        string="Email Template Definition",
    )
