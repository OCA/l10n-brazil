# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class SpedOperacao(models.Model):
    _inherit = 'sped.operacao'

    document_type_id = fields.Many2one(
        comodel_name='financial.document.type',
        string='Tipo de documento',
        ondelete='restrict',
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta contábil',
        ondelete='restrict',
        domain=[('is_brazilian_account', '=', True), ('tipo_sped', '=', 'A')],
    )
