# © 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def unlink(self):
        for record in self:
            payment_line_ids = record.line_ids.mapped("payment_line_ids")
            if any(
                state not in ["draft", "cancel"]
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
