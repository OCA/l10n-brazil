# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    sell_vacation = fields.Boolean(
        string=u'Sell Vacation',
        help=u'Indicates if the employee desires to sell some of its '
               u'entitled vacation days',
        default=False,
    )
    sold_vacations_days = fields.Integer(
        string=u'Sold Vacation Days',
        help=u'Number of vacation days the employee desires to sell',
        default=0,
    )
    vacations_days = fields.Integer(
        string=u'Number of vacation days',
    )
    advance_13_salary = fields.Boolean(
        string=u'Advance 13th salary',
        default=False,
    )
    advance_current_salary = fields.Boolean(
        string=u'Advance Currente Salary',
        default=False,
    )
    parent_id = fields.Many2one(
        comodel_name='hr.holidays',
        string=u'Worked Period',
        ondelete='restrict',
        index=True,
    )

    @api.multi
    def onchange_date_to(self, date_to, date_from, sold_vacations_days):
        result = super(HrHolidays, self).onchange_date_to(date_to, date_from)
        result['value']['vacations_days'] = \
            result['value']['number_of_days_temp']
        if sold_vacations_days > 0:
            result['value']['number_of_days_temp'] += sold_vacations_days
        return result

    @api.multi
    def onchange_date_from(self, date_to, date_from, sold_vacations_days):
        result = super(HrHolidays, self).onchange_date_to(date_to, date_from)
        result['value']['vacations_days'] = \
            result['value']['number_of_days_temp']
        if sold_vacations_days > 0:
            result['value']['number_of_days_temp'] += sold_vacations_days
        return result

    @api.onchange('sell_vacation', 'sold_vacations_days', 'vacations_days')
    def _calculate_sum_vacation_days(self):
        for record in self:
            if record.sell_vacation:
                record.number_of_days_temp = \
                    record.sold_vacations_days + record.vacations_days
            else:
                record.sold_vacations_days = 0
                record.number_of_days_temp = record.vacations_days
