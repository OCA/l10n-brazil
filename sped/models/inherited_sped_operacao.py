# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class SpedOperacao(models.Model):
    _inherit = 'sped.operacao'

    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term',
        string='Forma de pagamento',
        ondelete='restrict',
        domain=[('forma_pagamento', '!=', False)],
    )
