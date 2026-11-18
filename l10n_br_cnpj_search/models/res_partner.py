# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _fields_sync(self, values):
        if self.env.context.get("_partners_skip_fields_sync"):
            return
        super()._fields_sync(values)
