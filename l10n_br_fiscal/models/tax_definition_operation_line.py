# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TaxDefinitionOperationLine(models.Model):
    _inherit = "l10n_br_fiscal.tax.definition"

    fiscal_operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line", string="Operation Line"
    )

    @api.constrains("fiscal_operation_line_id")
    def _check_fiscal_operation_line_id(self):
        for record in self:
            if record.fiscal_operation_line_id:
                domain = [
                    ("id", "!=", record.id),
                    (
                        "fiscal_operation_line_id",
                        "=",
                        record.fiscal_operation_line_id.id,
                    ),
                    ("tax_group_id", "=", record.tax_group_id.id),
                    ("tax_id", "=", record.tax_id.id),
                ]

                if record.env["l10n_br_fiscal.tax.definition"].search_count(domain):
                    raise ValidationError(
                        _(
                            "Tax Definition already exists "
                            "for this Operation Line and Tax Group !"
                        )
                    )
