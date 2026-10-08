# Copyright 2026 Engenere (<https://engenere.one>)
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class DfeDocument(models.Model):
    _inherit = "l10n_br_fiscal_dfe.document"

    # Header buttons of the NF-e list (display="always"): they run with or
    # without selected rows and act on the active company, like the DF-e
    # banner buttons did before Odoo 18 dropped banner_route.

    def action_dfe_mock_search_nfe(self):
        return self.env["res.company"].action_banner_search_all_nfe()

    def action_dfe_mock_toggle(self):
        return self.env["res.company"].action_toggle_dfe_mock_mode()

    def action_dfe_mock_reset_cooldown(self):
        return self.env["res.company"].action_reset_dfe_cooldown()
