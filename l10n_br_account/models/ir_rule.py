# Copyright (C) 2026 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class IrRule(models.Model):
    _inherit = "ir.rule"

    def _compute_domain_keys(self):
        return super()._compute_domain_keys() + ["allow_fiscal_access"]

    @api.model
    def _compute_domain(self, model_name, mode="read"):
        if model_name in ("account.move", "account.move.line"):
            return super(
                IrRule, self.with_context(allow_fiscal_access=True)
            )._compute_domain(model_name, mode)
        if model_name in (
            "l10n_br_fiscal.document",
            "l10n_br_fiscal.document.line",
        ) and self._context.get("allow_fiscal_access"):
            return []
        return super()._compute_domain(model_name, mode)
