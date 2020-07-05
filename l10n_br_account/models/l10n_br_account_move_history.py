# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons.l10n_br_fiscal.tools.misc import compute_message as cm


class MoveHistory(models.Model):

    _name = 'l10n_br_account.move.history'
    _inherit = 'l10n_br_fiscal.data.abstract'
    _description = 'Histórico Contábil'

    code = fields.Char(required=False)
    comment = fields.Text(
        string="History",
        required=True
    )

    test_comment = fields.Text(string="Test Comment")

    @api.multi
    def object_selection_values(self):
        return [('l10n_br_fiscal.document', "Fiscal Document"),
                ('l10n_br_fiscal.document.line', "Fiscal Document Line")]

    object_id = fields.Reference(
        string='Reference',
        selection=lambda self: self.object_selection_values(),
        ondelete="set null"
    )

    def action_test_message(self):
        vals = {
            'user': self.env.user,
            'ctx': self._context,
            'doc': self.object_id
        }
        self.test_comment = cm(self, vals)

    def compute_message(self, vals):
        return cm(self, vals)
