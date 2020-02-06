# -*- coding: utf-8 -*-
# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import unicode_literals

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EdocCceWizard(models.TransientModel):

    _name = b'edoc.cce.wizard'

    justificative = fields.Text('Justificativa', size=255, required=True)

    @api.constrains('justificative')
    @api.multi
    def _check_justificative(self):
        for record in self:
            if len(record.justificative) < 15:
                raise UserError(
                    _('Justificativa deve ter o tamanho mínimo de 15 '
                      'caracteres.')
                )

    @api.multi
    def doit(self):
        for wizard in self:
            obj_invoice = self.env['account.invoice'].browse(
                self.env.context['active_id'])
            obj_invoice.cce_invoice_online(wizard.justificative)
        return {'type': 'ir.actions.act_window_close'}
