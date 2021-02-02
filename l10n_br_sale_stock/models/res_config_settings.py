# Copyright (C) 2021 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_create_invoice_policy = fields.Selection(
        related='company_id.sale_create_invoice_policy',
        readonly=False
    )
