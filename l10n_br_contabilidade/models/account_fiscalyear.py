# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountFiscalYear(models.Model):
    _inherit = 'account.fiscalyear'

    sequence_id = fields.Many2one(
        'ir.sequence',
        string=u'Sequence',
        readonly=True,
        compute='_compute_sequence_id',
        store=True,
    )

    @api.depends('sequence_id')
    def _compute_sequence_id(self):
        if not self.sequence_id:
            self.sequence_id = self.env['ir.sequence'].create(
                {'name': 'account_move_sequence_'+self.name, 'implementation': 'no_gap'}).id
