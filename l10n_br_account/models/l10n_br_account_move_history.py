# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class MoveHistory(models.Model):

    _name = 'l10n_br_account.move.history'
    _inherit = 'l10n_br_fiscal.data.abstract'
    _description = 'Histórico Contábil'

    code = fields.Char(required=False)
    history = fields.Text(
        string="History",
        required=True
    )

    # TODO: Refactoring fiscal.comment to use the same engine, move it to l10n_br_base
