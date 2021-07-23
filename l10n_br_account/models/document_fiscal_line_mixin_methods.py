# Copyright (C) 2021  Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class FiscalDocumentLineMixinMethods(models.AbstractModel):
    _inherit = "l10n_br_fiscal.document.line.mixin.methods"

    def _prepare_fiscal_account_id(self):
        vals = {}
        account_id = (
            self.cfop_id.account_id
            or self.fiscal_operation_line_id.account_id
            or self.account_id
        )
        if account_id:
            vals["account_id"] = account_id.id

    def _prepare_br_fiscal_dict(self, default=False):
        vals = super()._prepare_br_fiscal_dict(default)

        if self.fiscal_operation_id and self.fiscal_operation_line_id:
            if self.fiscal_operation_line_id.account_id:
                vals["account_id"] = self.fiscal_operation_line_id.account_id.id
            if self.cfop_id.account_id:
                vals["account_id"] = self.cfop_id.account_id.id
        return vals
