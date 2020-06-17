# -*- coding: utf-8 -*-
# Copyright 2017 Akretion
# @author Renato Lima <renato.lima@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class PaymentMode(models.Model):
    _inherit = 'account.payment.mode'
    
    cnab_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string=u'Sequencia do CNAB')

