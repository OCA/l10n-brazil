# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class TaxDefinitionCFOP(models.Model):
    _inherit = "l10n_br_fiscal.tax.definition"
    _description = "Tax Definition CFOP"

    cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP")

    _sql_constraints = [(
        "fiscal_tax_definition_cfop_uniq",
        "unique (cfop_id, tax_group_id)",
        "Tax Definition already exists with this CFOP, Group !")]

    @api.onchange('cfop_id')
    def _onchange_cfop_id(self):
        if self.cfop_id:
            self.type_in_out = self.cfop_id.type_in_out
