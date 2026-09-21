# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

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
