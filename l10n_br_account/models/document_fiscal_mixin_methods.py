# Copyright (C) 2021  Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class FiscalDocumentMixinMethods(models.AbstractModel):
    _inherit = "l10n_br_fiscal.document.mixin.methods"

    def _prepare_br_fiscal_dict(self, default=False):
        vals = super()._prepare_br_fiscal_dict(default)

        if self.fiscal_operation_id:
            if self.fiscal_operation_id.journal_id:
                vals["journal_id"] = self.fiscal_operation_id.journal_id.id

            if self.fiscal_operation_id.account_id:
                vals["account_id"] = self.fiscal_operation_id.account_id.id

        return vals
