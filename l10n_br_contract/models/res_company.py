# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    contract_fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Default Fiscal Operation',
        required=False)
