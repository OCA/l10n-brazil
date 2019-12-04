# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from ..constants.fiscal import TAX_DOMAIN


class TaxGroup(models.Model):
    _name = "l10n_br_fiscal.tax.group"
    _order = "sequence, name, tax_domain"
    _description = "Tax Group"

    name = fields.Char(string="Name", required=True)

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        required=True,
        help="The sequence field is used to define "
        "order in which the tax lines are applied.",
    )

    tax_domain = fields.Selection(
        selection=TAX_DOMAIN, string="Tax Domain", required=True
    )

    tax_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.tax", inverse_name="tax_group_id", string="Taxes"
    )

    cst_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.cst", inverse_name="tax_group_id", string="CSTs"
    )

    _sql_constraints = [
        (
            "fiscal_tax_group_code_uniq",
            "unique (name)",
            "Tax Group already exists with this name !",
        )
    ]
