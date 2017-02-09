# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class FinancialCancel(models.TransientModel):

    _name = 'financial.cancel'
    _rec_name = 'reason'

    reason = fields.Text(
        string=u'Cancel reason',
        required=True,
        help=u'The reason will be saved in record history',
    )

    @api.multi
    def doit(self):
        for wizard in self:
            pass
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Action Name',  # TODO
            'res_model': 'result.model',  # TODO
            'domain': [('id', '=', result_ids)],  # TODO
            'view_mode': 'form,tree',
        }
        return action
