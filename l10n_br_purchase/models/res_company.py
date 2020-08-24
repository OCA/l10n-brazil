# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    purchase_fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Default Fiscal Operation for Purchase',
        domain=[
            ('state', '=', 'approved'),
            ('fiscal_type', '=', 'purchase')],
    )
