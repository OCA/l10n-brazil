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

                    if date_start < datetime.datetime.today():

                        date_end = date_start + relativedelta(years=1)
                        concessivo_inicio = date_end
                        concessivo_fim = date_end + relativedelta(years=1)
                        limite_gozo = concessivo_fim - relativedelta(days=30)
                        limite_aviso = limite_gozo - relativedelta(days=30)

                        vacation_id = self.env.ref(
                            'l10n_br_hr_vacation.holiday_status_vacation').id
                        self.env['hr.holidays'].create({
                            'name': 'Periodo Aquisitivo: %s ate %s'
                                    % (date_start.date(), date_end.date()),
                            'employee_id': employee.id,
                            'holiday_status_id': vacation_id,
                            'type': 'add',
                            'holiday_type': 'employee',
                            'vacations_days': 30,
                            'sold_vacations_days': 0,
                            'number_of_days_temp': 30,
                            'contract_id': employee.contract_ids.id,
                        })
                        employee.end_last_vacation = date_end
