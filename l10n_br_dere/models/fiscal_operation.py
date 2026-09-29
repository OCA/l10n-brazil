# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants import TP_ATIV


class FiscalOperation(models.Model):
    _inherit = "l10n_br_fiscal.operation"

    l10n_br_dere_deductible = fields.Boolean(
        string="DeRE deductible",
        help="Inbound documents of this operation are loaded into D-1121.",
    )
    l10n_br_dere_tp_ativ = fields.Selection(
        TP_ATIV,
        string="DeRE deduction activity",
        help="Overrides the company default when loading D-1121 deductions.",
    )

    @api.constrains("l10n_br_dere_deductible", "fiscal_operation_type")
    def _check_dere_deductible_inbound(self):
        for rec in self:
            if rec.l10n_br_dere_deductible and rec.fiscal_operation_type == "out":
                raise ValidationError(
                    _("DeRE deductions apply only to inbound fiscal operations.")
                )
