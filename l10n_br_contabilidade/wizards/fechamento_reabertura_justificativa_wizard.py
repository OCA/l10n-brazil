# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)

from openerp import api, fields, models


class FechamentoReaberturaJustificativaWizard(models.TransientModel):
    _name = 'fechamento.reabertura.justificativa.wizard'

    reason = fields.Text(u'Justificativa', size=255, required=True)

    def _get_justificativa_values(self, fechamento_id):
        vals = {
            'employee_id': self.env.user.employee_ids.id,
            'data': fields.Date.today(),
            'motivo': self.reason,
            'fechamento_id': fechamento_id,
        }

        return vals

    @api.multi
    def action_confirm_reabrir(self):
        self.ensure_one()
        fechamento = self.env['account.fechamento'].browse(
            self.env.context['active_id'])
        vals = self._get_justificativa_values(fechamento.id)
        justificativa = self.env[
            'account.fechamento.reabertura.justificativa'].create(vals)
        fechamento.button_goback(justificativa_id=justificativa)
        return {'type': 'ir.actions.act_window_close'}
