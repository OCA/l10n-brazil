# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class ResCountryState(models.Model):
    _inherit = "res.country.state"
    _nfe_search_keys = ['ibge_code', 'code']
    _nfe_extra_domain = [('ibge_code', '!=', False)]
