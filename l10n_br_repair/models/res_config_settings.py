# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    copy_repair_quotation_notes = fields.Boolean(
        string='Copy repair quotation notes in Fiscal documents',
        related='company_id.copy_repair_quotation_notes',
        readonly=False,
    )
