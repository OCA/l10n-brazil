# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from ..constants.payment import (
    FORMA_PAGAMENTO,
    FORMA_PAGAMENTO_OUTROS,
)


class FiscalPaymentMode(models.Model):

    _name = 'l10n_br_fiscal.payment.mode'
    _description = 'Forma de Pagamento'
    _table = 'account_payment_mode'

    name = fields.Char()
    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        string='Forma de pagamento',
        default=FORMA_PAGAMENTO_OUTROS,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        ondelete='restrict',
        default=lambda self: self.env['res.company']._company_default_get(
            'l10n_br_fiscal.payment.mode'
        )
    )
