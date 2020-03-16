# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class MoveHistory(models.Model):

    _name = 'l10n_br_account.move.history'
    _inherit = 'l10n_br_fiscal.data.abstract'
    _description = 'Histórico Contábil'

    code = fields.Char(required=False)

