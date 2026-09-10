# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class Uom(models.Model):
    _inherit = "uom.uom"
    _nfe_search_keys = ["code"]

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        """Match a UoM by code, then by fuzzy name, never create.

        Some XMLs use a supplier abbreviation (e.g. ``uCom='MIL'``) that only
        matches the company UoM by name (``MILHEI``), hence the name_search
        fallback kept for backward compatibility. Creation is prevented by the
        ``spec_create_forbidden_models`` context key set by the import caller,
        so falling through to super() leaves the UoM unset instead of creating
        a partial record.
        """
        if rec_dict.get("code"):
            match = self.search([("code", "=", rec_dict.get("code"))], limit=1)
            if match:
                return match.id
            match = self.name_search(rec_dict.get("code"), limit=1)
            if match:
                return match[0][0]
        return super().match_or_create_m2o(rec_dict, parent_dict, model)
