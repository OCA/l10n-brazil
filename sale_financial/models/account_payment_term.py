# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    vende_acima_limite_cliente = fields.Boolean(
        string=u'Vender acima do limite de crédito?',
        default=False,
    )
