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
        default='ocorrencias',
    )
    holiday_status_id = fields.Many2one(
        domain="[('tipo', '=', tipo)]",
    )
    contrato_id = fields.Many2one(
        comodel_name='hr.contract',
        string=u'Contrato Associado',
    )

    @api.onchange('contrato_id')
    def onchange_contrato(self):
        for holiday in self:
            holiday.employee_id = holiday.contrato_id.employee_id
            holiday.department_id = holiday.contrato_id.departamento_lotacao

    @api.constrains('attachment_ids', 'holiday_status_id', 'date_from',
                    'date_to', 'number_of_days_temp')
    def validate_days_status_id(self):
        for record in self:
            if record.type == 'remove':
                # Validar anexo
                if record.need_attachment:
                    if not record.attachment_ids:
                        raise UserError(_("Atestado Obrigatório!"))
                # Validar Limite de dias
                if record.holiday_status_id.days_limit:
                    if record.holiday_status_id.type_day == u'uteis':
                        resource_calendar_obj = self.env['resource.calendar']
                        date_to = fields.Date.from_string(record.date_to)
                        date_from = fields.Date.from_string(record.date_from)
                        if resource_calendar_obj.quantidade_dias_uteis(
                                date_from, date_to) > \
                                record.holiday_status_id.days_limit:
                            raise UserError(_("Number of days exceeded!"))
                    if record.holiday_status_id.type_day == u'corridos':
                        if record.number_of_days_temp > \
                                record.holiday_status_id.days_limit:
                            raise UserError(_("Number of days exceeded!"))
                # Validar Limite de Horas
                if record.holiday_status_id.hours_limit:
                    if fields.Datetime.from_string(record.date_to) - \
                            fields.Datetime.from_string(record.date_from) > \
                            timedelta(minutes=60 *
                                      record.holiday_status_id.hours_limit):
                        raise UserError(_("Number of hours exceeded!"))

    @api.onchange('payroll_discount', 'holiday_status_id')
    def _set_payroll_discount(self):
        self.payroll_discount = self.holiday_status_id.payroll_discount

    @api.multi
    def get_ocurrences(self, employee_id, data_from, data_to):
        """Calcular a quantidade de faltas/ocorrencias que devem ser
        descontadas da folha de pagamento em determinado intervalo de tempo.
        :param  employee_id: Id do funcionario
                str data_from: Data inicial do intervalo de tempo.
                str data_end: Data final do intervalo
        :return dict {
                    - int faltas_remuneradas: Quantidade de faltas que devem
                    ser remuneradas dentro do intervalo passado como parâmetro
                    - int faltas_nao_remuneradas: Quantidade de faltas que NAO
                    serao remuneradas. (Descontadas da folha de pagamento)
        }
        """
        faltas = {
            'faltas_remuneradas': [],
            'quantidade_dias_faltas_remuneradas': 0,
            'faltas_nao_remuneradas': [],
            'quantidade_dias_faltas_nao_remuneradas': 0,
        }
        domain = [
            ('state', '=', 'validate'),
            ('employee_id', '=', employee_id),
            ('type', '=', 'remove'),
            ('date_from', '>=', data_from),
            ('date_to', '<=', data_to),
        ]
        holidays_ids = self.env['hr.holidays'].search(domain)

        for leave in holidays_ids:
            if leave.payroll_discount:
                faltas['faltas_nao_remuneradas'].append(leave)
                faltas['quantidade_dias_faltas_nao_remuneradas'] += \
                    leave.number_of_days_temp
            else:
                faltas['faltas_remuneradas'].append(leave)
                faltas['quantidade_dias_faltas_remuneradas'] += \
                    leave.number_of_days_temp
        return faltas

    @api.multi
    def holidays_validate(self):
        super(HrHolidays, self).holidays_validate()
        model_obj_id = self.env.ref("hr_holidays.model_hr_holidays").id
        self.meeting_id.write(
            {
                'models_id': model_obj_id,
                'class': 'private',
            }
        )
        return True
