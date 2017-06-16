# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class SpedOperacao(models.Model):
    _inherit = 'sped.operacao'

    financial_document_type_id = fields.Many2one(
        comodel_name='financial.document.type',
        string='Tipo de documento',
        ondelete='restrict',
    )
    financial_account_id = fields.Many2one(
        comodel_name='financial.account',
        string='Conta financeira',
        ondelete='restrict',
        domain=[('type', '=', 'A')],
    )
