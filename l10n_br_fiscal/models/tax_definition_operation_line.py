# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models


class TaxDefinitionOperationLine(models.Model):
    _inherit = "l10n_br_fiscal.tax.definition"

    operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line")

    _sql_constraints = [(
        "fiscal_tax_definition_operation_line_group_uniq",
        "unique (operation_line_id, tax_group_id)",
        _("Tax Definition already exists for this Operation Line and Group !"),
    )]
