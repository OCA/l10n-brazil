# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pytz
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from pybrasil import feriado
except ImportError:
    _logger.info('Cannot import pybrasil')

_INTERVALS = {
    'days': lambda interval: relativedelta(days=interval),
    'weeks': lambda interval: relativedelta(days=7*interval),
    'months': lambda interval: relativedelta(months=interval),
    'years': lambda interval: relativedelta(months=12*interval),
}


class PyBrasilHolidayImport(models.TransientModel):

    _name = 'wizard.pybrasil.holiday.import'

    @api.multi
    @api.depends('start_date', 'interval_number', 'interval_type')
    def _compute_end_date(self):
        for wiz in self:
            wiz.end_date = fields.Date.from_string(wiz.start_date) + \
                _INTERVALS[wiz.interval_type](wiz.interval_number)

    start_date = fields.Date(
        string='Start Date',
        default=fields.Date.today,
        readonly=1,
    )
    end_date = fields.Date(
        string='End Date',
        compute='_compute_end_date'
    )
    interval_number = fields.Integer(
        string='Interval',
        default=1
    )
    interval_type = fields.Selection([
        ('days', 'Day(s)'),
        ('weeks', 'Week(s)'),
        ('months', 'Month(s)'),
        ('years', 'Year(s)')],
        string='Type',
        default='days',
        required=True
    )
    calendar_id = fields.Many2one(
        'resource.calendar',
        string="Work Time"
    )

    @api.multi
    def get_state_from_calendar(self, holiday):
        state = self.env['res.country.state'].search(
            [('ibge_code', '=', holiday.estado.codigo_ibge)])
        return state or False

    @api.multi
    def get_country_from_calendar(self, holiday):
        country = self.env.ref("base.br")
        return country or False

    @api.multi
    def get_calendar_for_country(self):
        country = self.env.ref("base.br")
        if not self.env['resource.calendar'].search_count(
                [('country_id', '=', country.id)]):
            calendar = self.env['resource.calendar'].create({
                'name': 'Calendar ' + country.name,
                'country_id': country.id
                # '':u'N',
            })
            return calendar
        else:
            return self.env['resource.calendar'].search(
                [('country_id', '=', country.id)])[0]

    @api.multi
    def get_calendar_for_state(self, holiday):
        state = self.get_state_from_calendar(holiday)
        if not self.env['resource.calendar'].search_count(
                [('state_id', '=', state.id)]):
            parent_id = self.get_calendar_for_country()
            calendar_id = self.env['resource.calendar'].create({
                'name': 'Calendar ' + state.name,
                'state_id': state.id,
                'country_id': self.get_country_from_calendar(holiday).id,
                'parent_id': parent_id.id,
            })
            return calendar_id
        else:
            return self.env['resource.calendar'].search(
                [('state_id', '=', state.id)])[0]

    @api.multi
    def get_calendar_for_city(self, holiday):
        if not self.env['l10n_br_base.city'].search_count(
                [('ibge_code', '=', holiday.municipio.codigo_ibge)]):
            city_id = self.env['l10n_br_base.city'].create({
                'name': holiday.municipio.nome,
                'state_id': self.get_state_from_calendar(holiday).id,
                'ibge_code': holiday.municipio.codigo_ibge,
            })
        else:
            city_id = self.env['l10n_br_base.city'].search(
                [('ibge_code', '=', holiday.municipio.codigo_ibge)])

        if not self.env['resource.calendar'].search_count(
                [('l10n_br_city_id', '=', city_id.id)]):
            parent_id = self.get_calendar_for_state(holiday)

            calendar_id = self.env['resource.calendar'].create({
                'name': 'Calendar ' + holiday.municipio.nome,
                'l10n_br_city_id': city_id.id,
                'parent_id': parent_id.id,
                'state_id': self.get_state_from_calendar(holiday).id,
                'country_id': self.get_country_from_calendar(holiday).id,
            })
            return calendar_id
        else:
            return self.env['resource.calendar'].search(
                [('l10n_br_city_id', '=', city_id.id)])[0]

    @api.multi
    def holiday_import(self):
        tz_br = pytz.timezone('America/Sao_Paulo')

        for wiz in self:
            leaves = self.env['resource.calendar.leaves']
            public_holidays = []
            date_reference = fields.Date.from_string(wiz.start_date)

            while date_reference.year <= \
                    fields.Date.from_string(wiz.end_date).year:
                all_holidays = feriado.monta_dicionario_datas(
                    date_reference).items()
                for holiday in all_holidays:
                    if fields.Date.from_string(wiz.end_date) >= holiday[0] >= \
                            fields.Date.from_string(wiz.start_date):
                        public_holidays.append(holiday)

                for holidays in public_holidays:
                    utc_dt = fields.Datetime.from_string(
                        fields.Datetime.to_string(holidays[0]))

                    # Setar a data do feriado com timezone de brasilia
                    user_dt = tz_br.localize(utc_dt)
                    datetime_from = utc_dt - \
                        relativedelta(
                            seconds=user_dt.utcoffset().total_seconds())
                    datetime_to = datetime_from + relativedelta(days=1) - \
                        relativedelta(seconds=1)

                    date_from = fields.Datetime.to_string(datetime_from)
                    date_to = fields.Datetime.to_string(datetime_to)

                    for holiday in holidays[1]:
                        if holiday.abrangencia == u'N':  # Tipo Nacional
                            work_time = self.get_calendar_for_country()
                        if holiday.abrangencia == u'E':  # Tipo Estadual
                            work_time = self.get_calendar_for_state(holiday)
                        if holiday.abrangencia == u'M':  # Tipo Municipal
                            work_time = self.get_calendar_for_city(holiday)
                        if not leaves.search_count([
                                ('resource_id', '=', False),
                                ('calendar_id', '=', work_time.id),
                                ('date_from', '>=', date_from),
                                ('date_to', '<=', date_to)]):
                            leaves.create({
                                'resource_id': False,
                                'name': '%s %d' % (holiday.nome,
                                                   holidays[0].year),
                                'calendar_id': work_time.id,
                                'date_from': date_from,
                                'date_to': date_to,
                                'leave_type': holiday.tipo,
                                'abrangencia': holiday.abrangencia,
                            })
                date_reference += relativedelta(years=1)
        return True
