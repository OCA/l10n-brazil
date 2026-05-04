# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    sale_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Standard Sales Fiscal Operation",
    )

    copy_note = fields.Boolean(
        string="Copy Sale note on invoice",
        default=False,
    )
