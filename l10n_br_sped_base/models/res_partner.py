# Copyright 2025 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    is_accountant = fields.Boolean(string="Is accountant?")

    crc_code = fields.Char(string="CRC Code", size=18, unaccent=False)

    crc_state_id = fields.Many2one(comodel_name="res.country.state", string="CRC State")

    def _get_sped_cod_part(self):
        """COD_PART of the participant: the one rule of the 0150 and of every
        register that points to it (C100, C500, D100...). The id is unique
        per participant, which a CNPJ is not (branches, foreign partners,
        individuals without a document)."""
        self.ensure_one()
        return str(self.id)
