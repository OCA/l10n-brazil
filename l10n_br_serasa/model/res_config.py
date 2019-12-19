# Copyright 2015 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfig(models.Model):
    _inherit = "account.config.settings"

    logon_serasa = fields.Char(string="Login", related="company_id.logon_serasa")
    senha_serasa = fields.Char(string="Senha", related="company_id.senha_serasa")
