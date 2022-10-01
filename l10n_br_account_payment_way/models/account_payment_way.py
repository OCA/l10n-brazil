# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models


class AccountPaymentWay(models.Model):
    """Account Payment Way"""

    _name = "account.payment.way"
    _description = "Account Payment Way"

    PAYMENT_WAY_DOMAIN = [
        ("dinheiro", _("Dinheiro")),
        ("cheque", _("Cheque")),
        ("pix_transfer", _("PIX Transfer")),
        ("ted", _("TED")),
        ("doc", _("DOC")),
        ("boleto", _("Boleto")),
    ]

    name = fields.Char()
    domain = fields.Selection(string="Payment Way Domain", selection=PAYMENT_WAY_DOMAIN)
