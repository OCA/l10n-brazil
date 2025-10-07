from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    union_entity_code = fields.Char(string="Union Entity code", unaccent=False)
