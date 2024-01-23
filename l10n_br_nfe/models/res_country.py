# Copyright (C) 2022  Renan Hiroki Bastos - KMEE <renan.hiroki@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class Country(models.Model):
    _inherit = "res.country"
    _nfe_search_keys = ["bc_code"]

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        """If country not found, break hard, don't create it"""

        if rec_dict.get("bc_code"):
            domain = [("bc_code", "=", rec_dict.get("bc_code"))]
            match = self.search(domain, limit=1)
            if match:
                return match.id
        return False
