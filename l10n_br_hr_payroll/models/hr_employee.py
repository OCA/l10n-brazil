# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def write(self, vals):
        for dict_key in ['work_location', 'department_id', 'job_id',
                         'registration', 'manager']:
            if dict_key in vals:
                raise UserWarning(u'Alteração do campo %s só pode ser '
                                  u'realizada através do menu '
                                  u'Alterações Contratuais' % dict_key)
            else:
                return super(HrEmployee, self).write(vals)
