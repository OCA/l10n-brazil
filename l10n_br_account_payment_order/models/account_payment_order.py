# Copyright (C) 2020 - KMEE (<http://kmee.com.br>).
#  author Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from .account_payment_mode import OPERATION_TYPE


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    operation_type = fields.Selection(
        selection=OPERATION_TYPE,
        string='Tipo de Operação',
        related='payment_mode_id.operation_type',
        store=True
    )
