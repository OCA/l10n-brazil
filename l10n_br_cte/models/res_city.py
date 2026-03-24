# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResCity(models.Model):
    _inherit = "res.city"
    _cte_search_keys = ["ibge_code"]

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        """If city not found, break hard, don't create it"""

        if rec_dict.get("ibge_code"):
            domain = [("ibge_code", "=", rec_dict.get("ibge_code"))]
            match = self.search(domain, limit=1)
            if match:
                return match.id
        return False
