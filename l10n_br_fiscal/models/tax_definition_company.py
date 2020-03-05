# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models


class TaxDefinitionCompany(models.Model):
    _inherit = "l10n_br_fiscal.tax.definition"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company")

    _sql_constraints = [(
        "fiscal_tax_definition_company_group_uniq",
        "unique (company_id, tax_group_id)",
        _("Tax Definition already exists for this Company and Group !"),
    )]
