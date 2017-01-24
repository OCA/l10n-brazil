# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def write(self, vals):
        for dict_key in ['work_location', 'department_id', 'job_id',
                         'registration', 'manager']:
            if dict_key in vals:
                raise UserError(u'Alteração no campo %s só pode ser '
                                  u'realizada através do menu '
                                  u'Alterações Contratuais' % dict_key)

        return super(HrEmployee, self).write(vals)
