# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..constants.nfse_dfe import NFSE_ACCESS_KEY_SIZE


class DfeSpecificSearchWizard(models.TransientModel):
    _inherit = "dfe.specific.search.wizard"

    fiscal_type = fields.Selection(
        selection_add=[("nfse", "NFS-e")],
        ondelete={"nfse": "cascade"},
    )

    def _validate_access_key(self, key):
        if self.fiscal_type != "nfse":
            return super()._validate_access_key(key)
        if not key or len(key) != NFSE_ACCESS_KEY_SIZE or not key.isdigit():
            raise UserError(_("The NFS-e access key must have 50 digits."))
        return None
