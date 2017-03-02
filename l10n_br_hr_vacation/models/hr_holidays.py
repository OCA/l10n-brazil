# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp import api, models, fields

_logger = logging.getLogger(__name__)

try:
    from pybrasil import data
except ImportError:
    _logger.info('Cannot import pybrasil')


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
    sold_vacations_days_temp = fields.Integer(
        string=u'Sold Vacation Days',
        help=u'Number of vacation days the employee desires to sell',
        compute='_compute_days_temp',
    )
    vacations_days = fields.Integer(
        string=u'Number of vacation days',
    )
    vacations_days_temp = fields.Integer(
        string=u'Number of vacation days temp',
        compute='_compute_days_temp',
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
    controle_ferias = fields.Many2many(
        comodel_name='hr.vacation.control',
        relation='vacation_control_holidays_rel',
        column1='holiday_id',
        column2='hr_vacation_control_id',
        string=u'Controle de Férias',
    )
    regular = fields.Boolean(
        string=u'Regular',
        compute='verificar_regularidade',
    )

    @api.depends('parent_id')
    def verificar_regularidade(self):
        for holiday in self:
            if not holiday.parent_id:
                continue
            dias_de_direito = holiday.parent_id.number_of_days_temp
            dias_selecionados = holiday.number_of_days_temp
            if dias_de_direito < dias_selecionados:
                holiday.regular = False
            else:
                holiday.regular = True

    @api.depends('vacations_days', 'sold_vacations_days')
    def _compute_days_temp(self):
        for holiday_id in self:
            if holiday_id.type == 'remove':
                holiday_id.sold_vacations_days_temp = \
                    -holiday_id.sold_vacations_days
                holiday_id.vacations_days_temp = -holiday_id.vacations_days
            if holiday_id.type == 'add':
                holiday_id.vacations_days_temp = holiday_id.number_of_days_temp

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

    @api.onchange('parent_id')
    def _compute_contract(self):
        if self.parent_id:
            self.controle_ferias = self.parent_id.controle_ferias
            date_from = data.formata_data(self.date_from)
            date_to = data.formata_data(self.date_to)
            self.name =  \
                self.holiday_status_id.name + \
                ' [' + date_from + '-' + date_to + ']'
