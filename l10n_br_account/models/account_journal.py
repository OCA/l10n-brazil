# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    revenue_expense = fields.Boolean(
        string='Gera Financeiro',
    )
