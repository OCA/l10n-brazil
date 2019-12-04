# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from ..constants.fiscal import FISCAL_IN_OUT, FISCAL_OUT


class TaxDefinitionCFOP(models.Model):
    _name = "l10n_br_fiscal.tax.definition.cfop"
    _inherit = "l10n_br_fiscal.tax.definition.abstract"
    _description = "Tax Definition CFOP"

    cfop_id = fields.Many2one(comodel_name="l10n_br_fiscal.cfop", string="CFOP")

    type_in_out = fields.Selection(
        selection=FISCAL_IN_OUT,
        string="Type",
        related="cfop_id.type_in_out",
        default=FISCAL_OUT,
    )

    _sql_constraints = [
        (
            "fiscal_tax_definition_cfop_uniq",
            "unique (cfop_id, tax_group_id)",
            "Tax Definition already exists with this CFOP, Group !",
        )
    ]
