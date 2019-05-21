# -*- coding: utf-8 -*-
# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    payment_type = fields.Selection(
        selection_add=[
            ('cobranca', u'Cobrança'),
        ])
