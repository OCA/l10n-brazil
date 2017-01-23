# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
from dateutil.relativedelta import relativedelta
from openerp import api, models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    end_last_vacation = fields.Datetime(
        string='Ultimo dia da ultima ferias',
    )

    @api.model
    def function_vacation_verify(self):
        employees_ids = self.env['hr.employee'].search([('active', '=', True)])
        for employee in employees_ids:
                if employee.contract_ids:
                    if employee.end_last_vacation:
                        date_start = fields.Datetime.from_string(
                            employee.end_last_vacation)
                    else:
                        date_start = fields.Datetime.from_string(
                            employee.contract_ids.date_start)

                    if date_start + relativedelta(years=1) <  \
                            datetime.datetime.today():

                        vacation_id = self.env.ref(
                            'l10n_br_hr_vacation.holiday_status_vacation').id
                        self.env['hr.holidays'].create({
                            'name': 'Periodo Aquisitivo: %s ate %s'
                                    % (date_start, str(datetime.date.today())),
                            'employee_id': employee.id,
                            'holiday_status_id': vacation_id,
                            'type': 'add',
                            'holiday_type': 'employee',
                            'vacations_days': 30,
                            'sold_vacations_days': 0,
                            'number_of_days_temp': 30,
                        })
                        employee.end_last_vacation = datetime.datetime.today()
