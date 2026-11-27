# Copyright (C) 2021  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class TaxIpiGuideline(models.Model):
    _inherit = "l10n_br_fiscal.tax.ipi.guideline"
    _nfe_search_keys = ["code_unmasked"]

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        """If IpiGuideline not found, break hard, don't create it"""

        if rec_dict.get("code_unmasked"):
            domain = [("code_unmasked", "=", rec_dict.get("code_unmasked"))]
            match = self.search(domain, limit=1)
            if match:
                return match.id
        return False
