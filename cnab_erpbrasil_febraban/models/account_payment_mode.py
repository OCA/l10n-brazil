# -*- coding: utf-8 -*-
# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

from ..febraban.boleto.document import getBoletoSelection

boleto_selection = getBoletoSelection()


class AccountPaymentMode(models.Model):

    _inherit = 'account.payment.mode'

    boleto_type = fields.Selection(
        selection_add=boleto_selection
    )
