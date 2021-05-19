# Copyright (C) 2009  Renato Lima - Akretion
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class CountryState(models.Model):
    _inherit = "res.country.state"

    ibge_code = fields.Char(string="IBGE Code", size=2)
