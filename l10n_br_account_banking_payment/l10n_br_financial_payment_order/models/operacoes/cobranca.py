# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError
from openerp.addons.financial.constants import FINANCIAL_DEBT_2RECEIVE


class PaymentOrder(models.Model):
    _inherit = b'payment.order'

    def financial_payment_import(self):
        self.ensure_one()

        if self.tipo_pagamento == 'cobranca':
            financial_move_ids = self.env['financial.move'].search([
                ('company_id', '=', self.company_id.id),
                ('type', '=', FINANCIAL_DEBT_2RECEIVE),
                # ('document_type_id', '=', )
            ])

            print (financial_move_ids)

        result = super(PaymentOrder, self).financial_payment_import()

        return result