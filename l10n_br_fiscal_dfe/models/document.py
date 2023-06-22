# Copyright (C) 2023 KMEE Informatica LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    dfe_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.dfe",
        string="DF-e Consult",
    )
