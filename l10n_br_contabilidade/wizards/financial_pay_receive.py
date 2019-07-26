# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

from openerp import api, fields, models


class FinancialPayreceive(models.TransientModel):
    _inherit = 'financial.pay_receive'

    @api.multi
    def doit(self):
        for wizard in self:
            super(FinancialPayreceive, wizard).doit()

            active_id = wizard._context['active_id']

            financial_move = self.env['financial.move'].browse(active_id)
            financial_move.gerar_evento_contabil(wizard.date_payment)
