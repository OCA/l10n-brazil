# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)

from openerp import api, fields, models


class PeriodoReaberturaJustificativaWizard(models.TransientModel):
    _name = 'periodo.reabertura.justificativa.wizard'

    reason = fields.Text(u'Justificativa', size=255, required=True)

    def _get_justificativa_values(self, period_id):
        vals = {
            'employee_id': self.env.user.employee_ids.id,
            'data': fields.Date.today(),
            'motivo': self.reason,
            'period_id': period_id,
        }

        return vals

    @api.multi
    def action_confirm_reabrir(self):
        self.ensure_one()
        period_id = self.env['account.period'].browse(
            self.env.context['active_id'])
        vals = self._get_justificativa_values(period_id.id)
        self.env['account.reabertura.periodo.justificativa'].create(vals)
        period_id.state = 'validate'

        return {'type': 'ir.actions.act_window_close'}
