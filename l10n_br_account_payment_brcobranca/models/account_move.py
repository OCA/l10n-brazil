# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, fields, models


class AccountMoveCompletionRule(models.Model):
    """
        Add a relation to CNAB Return Log File used to generate the move.
    """

    _inherit = 'account.move'

    cnab_return_log_id = fields.Many2one(
        string='CNAB Return Log', comodel_name='cnab.return.log',
        readonly=True, inverse_name='move_id'
    )
