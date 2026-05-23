# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class Operation(models.Model):
    _inherit = "l10n_br_fiscal.operation"

    operation_subsequent_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.subsequent.operation",
        inverse_name="fiscal_operation_id",
        string="Subsequent Operation",
    )

    @api.onchange("operation_subsequent_ids")
    def _onchange_operation_subsequent_ids(self):
        for sub_operation in self.operation_subsequent_ids:
            sub_operation.fiscal_operation_id = self.id
