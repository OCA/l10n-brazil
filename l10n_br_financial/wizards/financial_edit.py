# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FinancialEdit(models.TransientModel):

    _name = 'financial.edit'

    name = fields.Char()

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
    )
    amount_document = fields.Monetary(
        string=u"Document amount",
        required=True,
    )
    due_date = fields.Date(
        string=u"Due date",
        required=True,
    )
    change_reason = fields.Text(
        string="Change reason",
        track_visibility='onchange',
        required=True,
    )

    @api.model
    def default_get(self, fields):
        res = super(FinancialEdit, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        if (self.env.context.get('active_model') == 'financial.move' and
                active_id):
            fm = self.env['financial.move'].browse(active_id)
            res['currency_id'] = fm.currency_id.id
            res['amount_document'] = fm.amount_document
            res['due_date'] = fm.due_date
        return res

    def doit(self):
        for wizard in self:
            active_id = self._context['active_id']
            if (self.env.context.get('active_model') == 'financial.move' and
                    active_id):
                fm = self.env['financial.move'].browse(active_id)
                fm.write({
                    'currency_id': wizard.currency_id.id,
                    'amount_document': wizard.amount_document,
                    'due_date': wizard.due_date,
                    'change_reason': wizard.change_reason,
                })
        # return True
        return {'type': 'ir.actions.act_window_close', }
