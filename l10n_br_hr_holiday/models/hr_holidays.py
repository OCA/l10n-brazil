# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta
from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

OCORRENCIA_TIPO = [
    ('ferias', u'Férias'),
    ('ocorrencias', u'Ocorrências'),
    ('compensacao', u'Compensação de Horas'),
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
        string=u'Descontar dia no Holerite?',
        help=u'Na ocorrência desse evento, será descontado em folha a '
             u'quantidade de dias em afastamento.',
    )
    descontar_DSR = fields.Boolean(
        string=u'Descontar DSR',
        help=u'Descontar DSR da semana de ocorrência do evento?',
    )

    tipo = fields.Selection(
        selection=OCORRENCIA_TIPO,
        string="Tipo",
    )

    holiday_status_id = fields.Many2one(
        domain="[('tipo', '=', tipo)]",
    )
    contrato_id = fields.Many2one(
        comodel_name='hr.contract',
        string=u'Contrato Associado',
    )

    department_id=fields.Many2one(
        string="Departamento/lotação",
        comodel_name='hr.department',
        compute='_compute_department_id',
        store=True,
    )

    @api.multi
    @api.onchange('holiday_status_id')
    def _onchange_tipo(self):
        """
        Definir o tipo de holidays baseado no tipo do holidays_status
        :return:
        """
        for record in self:
            if record.holiday_status_id and record.holiday_status_id.tipo:
                record.tipo = record.holiday_status_id.tipo

    @api.depends('contrato_id')
    def _compute_department_id(self):
        for holiday in self:
            if holiday.contrato_id:
                holiday.department_id = holiday.contrato_id.department_id

    @api.onchange('contrato_id')
    def onchange_contrato(self):
        for holiday in self:
            holiday.employee_id = holiday.contrato_id.employee_id

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
                # if record.holiday_status_id.hours_limit:
                #     if fields.Datetime.from_string(record.date_to) - \
                #             fields.Datetime.from_string(record.date_from) > \
                #             timedelta(minutes=60 *
                #                       record.holiday_status_id.hours_limit):
                #         raise UserError(_("Number of hours exceeded!"))

    @api.onchange('payroll_discount', 'holiday_status_id')
    def _set_payroll_discount(self):
        self.payroll_discount = self.holiday_status_id.payroll_discount
        self.descontar_DSR = self.holiday_status_id.descontar_DSR

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
        ]

        clause_1 = [('data_inicio', '>=', data_from), ('data_inicio', '<=', data_to)]
        holidays_1_ids = self.env['hr.holidays'].search(domain + clause_1)

        clause_2 = [('data_fim', '>=', data_from), ('data_fim', '<=', data_to)]
        holidays_2_ids = self.env['hr.holidays'].search(domain + clause_2)

        for leave in holidays_1_ids | holidays_2_ids:
            qtd_dias_dentro_mes = 0
            data_referencia = fields.Datetime.from_string(leave.data_inicio)
            data_fim_holidays = fields.Datetime.from_string(leave.data_fim)

            while data_referencia <= data_fim_holidays:
                if data_referencia >= fields.Datetime.from_string(data_from) and \
                        data_referencia <= fields.Datetime.from_string(data_to):
                    # Levar em consideração o tipo de dias
                    if leave.holiday_status_id.type_day == 'uteis':
                        rc = self.env['resource.calendar']
                        if rc.data_eh_dia_util(data_referencia):
                            qtd_dias_dentro_mes += 1
                    else:
                        qtd_dias_dentro_mes += 1
                data_referencia += timedelta(days=1)

            if leave.payroll_discount:
                faltas['faltas_nao_remuneradas'].append(leave)
                faltas['quantidade_dias_faltas_nao_remuneradas'] += \
                    qtd_dias_dentro_mes
            else:
                faltas['faltas_remuneradas'].append(leave)
                faltas['quantidade_dias_faltas_remuneradas'] += \
                    qtd_dias_dentro_mes
        return faltas

    @api.multi
    def holidays_validate(self):
        super(HrHolidays, self).holidays_validate()
        model_obj_id = self.env.ref("hr_holidays.model_hr_holidays").id
        self.meeting_id.write({
            'models_id': model_obj_id,
            'class': 'private',
        })
        return True
