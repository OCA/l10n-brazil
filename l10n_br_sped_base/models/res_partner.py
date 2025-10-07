# Copyright 2025 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    is_accountant = fields.Boolean(string="Is accountant?")

    crc_code = fields.Char(string="CRC Code", size=18, unaccent=False)

    crc_state_id = fields.Many2one(comodel_name="res.country.state", string="CRC State")
