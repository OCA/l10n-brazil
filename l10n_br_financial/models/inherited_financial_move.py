# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class FinancialMove(models.Model):

    _inherit = b'financial.move'

    tipo_documento_id = fields.Many2one(
        string='Tipo do documento',
        comodel_name=b'financeiro.tipo.documento',
    )

    @api.onchange('date')
    def computar_date_maturity(self):
        for move in self:
            if move.financial_type in ('money_in', 'money_out'):
                move.date_maturity = move.date
