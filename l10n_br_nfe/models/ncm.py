# Copyright (C) 2021  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class Ncm(models.Model):
    _inherit = "l10n_br_fiscal.ncm"
    _nfe_search_keys = ["code_unmasked"]

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        """The NCM table has one record per IPI exception sharing the same
        code, and the NF-e brings the exception in a separate tag (EXTIPI):
        match the NCM without exception instead of an arbitrary one."""
        if rec_dict.get("code_unmasked"):
            matches = self.search([("code_unmasked", "=", rec_dict["code_unmasked"])])
            match = matches.filtered(lambda ncm: not ncm.exception)[:1] or matches[:1]
            if match:
                return match.id
        return super().match_or_create_m2o(rec_dict, parent_dict, model=model)
