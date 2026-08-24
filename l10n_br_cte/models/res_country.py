# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResCountry(models.Model):
    _inherit = "res.country"
    _cte_search_keys = ["bc_code"]

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        """If country not found, break hard, don't create it"""

        if rec_dict.get("bc_code"):
            domain = [("bc_code", "=", rec_dict.get("bc_code"))]
            match = self.search(domain, limit=1)
            if match:
                return match.id
        return False
