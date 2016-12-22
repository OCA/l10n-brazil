# -*- coding: utf-8 -*-
# Copyright 2016 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class HrHolidays(models.Model):

    _inherit = 'hr.holidays'

    message = fields.Char(
        string=u"Mensagem",
        related='holiday_status_id.message',
    )

    def validate_days_status_id(self):
        resource_calendar_obj = self.env['resource.calendar']
        for record in self:
            if record.holiday_status_id.type_day:
                if record.holiday_status_id.type_day == u'uteis':
                   if resource_calendar_obj.retorna_num_dias_uteis(
                            datetime.strptime(
                                record.date_from,"%Y-%m-%d %H:%M:%S"),
                            datetime.strptime(
                                record.date_to,"%Y-%m-%d %H:%M:%S")
                    ) > record.holiday_status_id.days_limit:
                        raise UserError(_("Número de dias excedido!"))
                if record.holiday_status_id.type_day == u'corridos':
                    if record.number_of_days_temp > \
                            record.holiday_status_id.days_limit:
                        raise UserError(_("Número de dias excedido!"))

    @api.multi
    def holidays_confirm(self):
        self.validate_days_status_id()
        return super(HrHolidays, self).holidays_confirm()
