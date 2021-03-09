# © 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    cnab_return_log_id = fields.Many2one(
        string='CNAB Return Log',
        comodel_name='l10n_br_cnab.return.log',
        readonly=True,
        inverse_name='move_id'
    )

    # Usados para deixar invisivel o campo
    # relacionado ao CNAB na visao
    is_cnab = fields.Boolean(
        string='Is CNAB ?'
    )
