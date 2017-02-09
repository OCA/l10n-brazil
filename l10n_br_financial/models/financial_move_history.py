# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class FinancialMoveHistory(models.Model):

    _name = 'financial.move.history'
    _description = 'Financial Move History'  # TODO

    name = fields.Char()
    financial_move_id = fields.Many2one(
        comodel_name='financial.move',
    )