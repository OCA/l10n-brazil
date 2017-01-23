# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta
from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

OCORRENCIA_TIPO = [
    ('ferias', u'Férias'),
    ('ocorrencias', u'Ocorrências'),
]


class HrHolidays(models.Model):

    _inherit = 'hr.holidays'

    message = fields.Char(
        string=u"Mensagem",
        related='holiday_status_id.message',
    )
    need_attachment = fields.Boolean(
        string=u'Need attachment',
        related='holiday_status_id.need_attachment',
    )
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string=u'Justification'
    )
    payroll_discount = fields.Boolean(
        string=u'Payroll Discount',
    )
    tipo = fields.Selection(
        selection=OCORRENCIA_TIPO,
        string="Tipo",
        default='ferias',
    )
    holiday_status_id = fields.Many2one(
        domain="[('tipo', '=', tipo)]",
    )

    @api.constrains('attachment_ids', 'holiday_status_id', 'date_from',
                    'date_to', 'number_of_days_temp')
    def validate_days_status_id(self):
        # Validar anexo
        if self.need_attachment:
            if not self.attachment_ids:
                raise UserError(_("Atestado Obrigatório!"))
        resource_calendar_obj = self.env['resource.calendar']
        for record in self:
            if record.holiday_status_id.days_limit:
                if record.holiday_status_id.type_day == u'uteis':
                    if resource_calendar_obj.quantidade_dias_uteis(
                            fields.Datetime.from_string(record.date_from),
                            fields.Datetime.from_string(record.date_to)) > \
                            record.holiday_status_id.days_limit:
                        raise UserError(_("Number of days exceeded!"))
                if record.holiday_status_id.type_day == u'corridos':
                    if record.number_of_days_temp > \
                            record.holiday_status_id.days_limit:
                        raise UserError(_("Number of days exceeded!"))
            if record.holiday_status_id.hours_limit:
                if fields.Datetime.from_string(record.date_to) - \
                        fields.Datetime.from_string(record.date_from) > \
                        timedelta(minutes=60 *
                                  record.holiday_status_id.hours_limit):
                    raise UserError(_("Number of hours exceeded!"))

    @api.onchange('payroll_discount', 'holiday_status_id')
    def _set_payroll_discount(self):
        self.payroll_discount = self.holiday_status_id.payroll_discount
