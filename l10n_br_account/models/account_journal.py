# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    revenue_expense = fields.Boolean(
        string='Gera Financeiro',
    )
    auto_generate_moves = fields.Boolean(
        string='Generate Moves Automatically',
        groups='l10n_br_account.group_roteiros_contabeis',
    )
    post_account_moves = fields.Boolean(
        string='Post Moves Automatically',
        groups='l10n_br_account.group_roteiros_contabeis',
    )
    generate_move_with_templates = fields.Boolean(
        string='Generate moves with templates',
        groups='l10n_br_account.group_roteiros_contabeis',
    )
