# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from openerp import api, fields, models

MES_DO_ANO = [
    (1, u'Jan'),
    (2, u'Fev'),
    (3, u'Mar'),
    (4, u'Abr'),
    (5, u'Mai'),
    (6, u'Jun'),
    (7, u'Jul'),
    (8, u'Ago'),
    (9, u'Set'),
    (10, u'Out'),
    (11, u'Nov'),
    (12, u'Dez'),
]

TIPO_DE_FOLHA = [
    ('normal', u'Folha normal'),
    ('rescisao', u'Rescisão'),
    ('ferias', u'Férias'),
    ('decimo_terceiro', u'Décimo terceiro (13º)'),
    ('licenca_maternidade', u'Licença maternidade'),
    ('auxilio_doenca', u'Auxílio doença'),
    ('auxílio_acidente_trabalho', u'Auxílio acidente de trabalho'),
]


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    mes_do_ano = fields.Selection(
        selection=MES_DO_ANO,
        string=u'Mês',
        required=True,
        default=datetime.now().month,
    )
    ano = fields.Integer(
        string=u'Ano',
        default=datetime.now().year,
    )
    tipo_de_folha = fields.Selection(
        selection=TIPO_DE_FOLHA,
        string=u'Tipo de folha',
        default='normal',
    )
    contract_id = fields.Many2many(
        comodel_name='hr.contract',
        string='Contratos',
    )

    @api.multi
    @api.onchange('mes_do_ano')
    def buscar_datas_periodo(self):
        for record in self:
            record.set_dates()

    def set_dates(self):
        for record in self:
            ultimo_dia_do_mes = str(
                self.env['resource.calendar'].get_ultimo_dia_mes(
                    record.mes_do_ano, record.ano))

            primeiro_dia_do_mes = str(
                datetime.strptime(str(record.mes_do_ano) + '-' +
                                  str(record.ano), '%m-%Y'))

            record.date_start = primeiro_dia_do_mes
            record.date_end = ultimo_dia_do_mes

    @api.multi
    def gerar_holerites(self):
        for contrato in self.contract_id:
            payslip_obj = self.env['hr.payslip']
            payslip = payslip_obj.create(
                {
                    'contract_id': contrato.id,
                    'mes_do_ano': self.mes_do_ano,
                    'ano': self.ano,
                    'date_from': self.date_start,
                    'date_to': self.date_end,
                    'employee_id': contrato.employee_id.id,
                    'tipo_de_folha': self.tipo_de_folha,
                    'payslip_run_id': self.id,
                }
            )
            payslip.set_employee_id()
            payslip.onchange_employee_id(
                self.date_start,
                self.date_end,
                contrato.id
            )
            worked_days_line_ids = payslip.get_worked_day_lines(
                contrato.id, self.date_start, self.date_end
            )
            input_line_ids = payslip.get_inputs(
                contrato.id, self.date_start, self.date_end
            )
            worked_days_obj = self.env['hr.payslip.worked_days']
            input_obj = self.env['hr.payslip.input']
            for worked_day in worked_days_line_ids:
                worked_day.update({'payslip_id': payslip.id})
                worked_days_obj.create(worked_day)
            for input_id in input_line_ids:
                input_id.update({'payslip_id': payslip.id})
                input_obj.create(input_id)
            payslip.compute_sheet()
