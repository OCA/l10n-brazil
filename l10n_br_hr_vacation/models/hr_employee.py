# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
# from dateutil.relativedelta import relativedelta
from openerp import api, models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    end_last_vacation = fields.Char(
        string='Ultimo dia da ultima ferias',
    )

    @api.model
    def function_vacation_verify(self):
        employees_ids = self.env['hr.employee'].search([('active', '=', True)])
        for employee in employees_ids:
                if employee.contract_ids:
                    # print("Dias de trabalho do Funcionario = %s" %
                    # self._get_number_of_days(employee.contract_ids.date_start
                    # ,str(datetime.date.today())) )

                    if employee.end_last_vacation:
                        date_start = employee.end_last_vacation
                    else:
                        date_start = employee.contract_ids.date_start

                    # TO DO : Usar  relativedelta
                    if self._get_number_of_days(
                            date_start, str(datetime.date.today())) > 365:
                        # print("Vacation! for %s" % employee.display_name)
                        vacation_id = self.env.ref(
                            'l10n_br_hr_vacation.holiday_status_vacation').id
                        self.env['hr.holidays'].create(
                            {
                                'name': 'Periodo Aquisitivo: %s ate %s'
                                        % (date_start,
                                           str(datetime.date.today())),
                                'employee_id': employee.id,
                                'holiday_status_id': vacation_id,
                                'type': 'add',
                                'holiday_type': 'employee',
                                'vacations_days': 30,
                                'sold_vacations_days': 0,
                                'number_of_days_temp': 30,
                            }
                        )
                        employee.end_last_vacation = str(datetime.date.today())

    def _get_number_of_days(self, date_from, date_to):
        """Returns a float equals to the timedelta between
        two dates given as string."""
        DATETIME_FORMAT = "%Y-%m-%d"
        from_dt = datetime.datetime.strptime(date_from, DATETIME_FORMAT)
        to_dt = datetime.datetime.strptime(date_to, DATETIME_FORMAT)
        timedelta = to_dt - from_dt
        diff_day = timedelta.days + float(timedelta.seconds) / 86400
        return diff_day
