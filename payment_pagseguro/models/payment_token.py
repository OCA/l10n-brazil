# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentToken(models.Model):
    _inherit = "payment.token"

    pagseguro_card_brand = fields.Char(
        string="Card Brand",
        help="The brand of the card, as returned by PagBank.",
        readonly=True,
    )
