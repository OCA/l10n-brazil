# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OperationLine(models.Model):
    _inherit = "l10n_br_fiscal.operation.line"

    allow_tax_manual = fields.Boolean(
        string="Allow Manual Tax Override",
        help="Show the manual tax base/value fields on document lines using "
        "this fiscal operation line.",
    )
