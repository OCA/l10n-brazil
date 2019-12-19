# Copyright 2015 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    logon_serasa = fields.Char("Logon", size=8)
    senha_serasa = fields.Char("Senha", size=8)
