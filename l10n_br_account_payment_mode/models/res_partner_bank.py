# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.multi
    @api.constrains('bank_bic')
    def check_bic_length(self):
        '''
        sobrescrever constrains do core que não leva em consideração bancos
         que nao são internacionais.
        '''
        return True
