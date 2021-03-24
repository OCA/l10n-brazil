# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResCity(models.Model):
    _inherit = 'res.city'
    _nfe_search_keys = ['ibge_code']

    # TODO understand why this is still required
    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        "if city not found, break hard, don't create it"
        if parent_dict.get('nfe40_cMun') or parent_dict.get('nfe40_cMunFG'):
            ibge_code = parent_dict.get('nfe40_cMun',
                                        parent_dict.get('nfe40_cMunFG'))
            ibge_code = ibge_code[2:8]
            domain = [('ibge_code', '=', ibge_code)]
            match = self.search(domain, limit=1)
            if match:
                return match.id
        return False
