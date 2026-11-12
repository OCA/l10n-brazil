# Copyright 2026 Engenere.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class DfeSpecificSearchWizard(models.TransientModel):
    _inherit = "dfe.specific.search.wizard"

    @api.model
    def default_get(self, fields_list):
        # CTeDistribuicaoDFe has no consChCTe: only the NSU search applies.
        vals = super().default_get(fields_list)
        if vals.get("fiscal_type") == "cte":
            vals["search_type"] = "nsu"
        return vals

    def action_confirm_search(self):
        self.ensure_one()
        if self.fiscal_type == "cte" and self.search_type == "access_key":
            raise UserError(
                _(
                    "The CT-e distribution service does not support searching "
                    "by access key. Search by NSU instead."
                )
            )
        return super().action_confirm_search()
