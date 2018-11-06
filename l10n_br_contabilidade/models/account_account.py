# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models

class Accountaccount(models.Model):
    _inherit = 'account.account'

    @api.multi
    def verificar_contas(self):
        """
        :return:
        """
        pass
