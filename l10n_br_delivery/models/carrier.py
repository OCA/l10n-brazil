# Copyright (C) 2010  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class Carrier(models.Model):
    _inherit = 'delivery.carrier'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Transportadora',
        domain=[('supplier', '=', True)],
    )

    antt_code = fields.Char(
        string='Codigo ANTT',
        size=32,
    )
