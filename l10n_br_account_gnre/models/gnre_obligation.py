# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class GnreObligation(models.Model):
    """Liga a obrigação à fatura de origem e à fatura de pagamento.

    Os dois campos moram aqui, e não no `l10n_br_gnre`, porque `account` é
    dependência deste módulo e não daquele. O `l10n_br_gnre` fica instalável
    sem contabilidade, no mesmo desenho de `l10n_br_nfe` e `l10n_br_account_nfe`.
    """

    _inherit = "l10n_br_gnre.obligation"

    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Fatura de Origem",
        ondelete="cascade",
        index=True,
        copy=False,
    )

    payable_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Fatura a Pagar",
        readonly=True,
        copy=False,
        help="Conta a pagar contra a Secretaria da Fazenda favorecida.",
    )
