# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields

from ..constants.fiscal import (
    FISCAL_IN_OUT,
    FISCAL_OUT)


class TaxDefinitionCompany(models.Model):
    _name = 'l10n_br_fiscal.tax.definition.company'
    _inherit = 'l10n_br_fiscal.tax.definition.abstract'
    _description = 'Tax Definition Company'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company')

    type_in_out = fields.Selection(
        selection=FISCAL_IN_OUT,
        string='Type',
        default=FISCAL_OUT)

    _sql_constraints = [
        ('fiscal_tax_definition_cfop_uniq',
         'unique (company_id, tax_group_id)',
         'Tax Definition already exists for this Company and Group !')]
