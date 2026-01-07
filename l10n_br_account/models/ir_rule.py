# Copyright (C) 2026 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models, tools
from odoo.tools import config


class IrRule(models.Model):
    _inherit = "ir.rule"

    @api.model
    @tools.conditional(
        "xml" not in config["dev_mode"],
        tools.ormcache(
            "self.env.uid",
            "self.env.su",
            "model_name",
            "mode",
            "tuple(self._compute_domain_context_values())",
        ),
    )
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
