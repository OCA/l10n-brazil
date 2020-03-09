# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TaxDefinitionOperationLine(models.Model):
    _inherit = "l10n_br_fiscal.tax.definition"

    operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line")

    @api.multi
    @api.constrains("operation_line_id")
    def _check_operation_line_id(self):
        for record in self:
            if record.operation_line_id:
                domain = [
                    ("id", "!=", record.id),
                    ('operation_line_id', '=', record.operation_line_id.id),
                    ('tax_group_id', '=', record.tax_group_id.id)]

                if record.env["l10n_br_fiscal.tax.definition"].search(domain):
                    raise ValidationError(_(
                        "Tax Definition already exists "
                        "for this Operation Line and Tax Group !"))
