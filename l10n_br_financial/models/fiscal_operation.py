# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class Operation(models.Model):
    _inherit = 'l10n_br_fiscal.operation'

    financial_account_id = fields.Many2one(
        comodel_name='financial.account',
        string='Financial Account',
        company_dependent=True,
    )

