# Copyright (C) 2015  Luis Felipe Miléo - KMEE
# Copyright (C) 2016  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class ResCountryState(models.Model):
    _inherit = "res.country.state"
