# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from ..constants.payment import (
    FORMA_PAGAMENTO,
    FORMA_PAGAMENTO_OUTROS,
)


class FiscalPaymentMode(models.Model):

    _name = 'l10n_br_fiscal.payment.mode'
    _description = 'Forma de Pagamento'
    # _table = 'account_payment_mode'

    name = fields.Char()
    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        string='Forma de pagamento',
        default=FORMA_PAGAMENTO_OUTROS,
    )
