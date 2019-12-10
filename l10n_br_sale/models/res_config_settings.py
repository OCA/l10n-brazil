# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    copy_note = fields.Boolean(
        string="Copiar Observações nos Documentos Fiscais",
        related="company_id.copy_note",
        readonly=False
    )
