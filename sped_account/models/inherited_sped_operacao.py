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

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Diário',
        domain=[('is_brazilian', '=', True)],
    )
    account_move_template_ids = fields.Many2many(
        comodel_name='sped.account.move.template',
        relation='sped_account_move_template_operacao',
        column1='operacao_id',
        column2='template_id',
        string='Modelo de partidas dobradas',
    )
