# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons.l10n_br_financial.models.financial_move_model import (
    FINANCIAL_MOVE
)


class FinancialMoveCreate(models.TransientModel):

    _name = 'financial.move.create'
    _inherit = ['financial.move.model']

    def _readonly_state(self):
        return {
            'draft': [('readonly', False)],
            'computed': [('readonly', False)],
        }

    move_type = fields.Selection(
        selection=FINANCIAL_MOVE
    )
    line_ids = fields.One2many(
        comodel_name='financial.move.line.create',
        inverse_name='financial_move_id',
        readonly=True,
    )

    state = fields.Selection(
        selection=[
            ('draft', u'Draft'),
            ('computed', u'Computed'),
        ],
        string='Status',
        index=True,
        readonly=True,
        default='draft',
        track_visibility='onchange',
        copy=False,
    )

    @api.multi
    def doit(self):
        for wizard in self:
            # fm = self.env['financial.move']
            # TODO
            pass

        if wizard.move_type == 'r':
            action = 'financial_receivable_act_window'
        else:
            action = 'financial_payable_act_window'
        action = {
            'type': 'ir.actions.act_window',
            'name': action,  # TODO
            'res_model': 'financial.move',
            # 'domain': [('id', '=', result_ids)],f
            'view_mode': 'tree,form',
        }
        return action


class FinancialMoveLineCreate(models.TransientModel):

    _name = 'financial.move.line.create'
    _inherit = ['financial.move.model']

    financial_move_id = fields.Many2one(
        comodel_name='financial.move.create',
    )
