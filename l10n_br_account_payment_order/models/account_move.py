# © 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models, fields
from odoo.exceptions import ValidationError


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

    @api.multi
    def unlink(self):
        for record in self:
            payment_line_ids = record.line_ids.mapped("payment_line_ids")
            if any(
                state not in ("draft", "cancel")
                for state in payment_line_ids.mapped("state")
            ):
                raise ValidationError(
                    _(
                        "Não foi possível cancelar a fatura, pois existem linhas "
                        "de pagamentos ativas vinculadas ao lançamento de diário"
                        "dela."
                    )
                )
            payment_line_ids.unlink()
        return super().unlink()
