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
    ('decimo_terceiro', u'Décimo terceiro (13º)'),
    ('provisao_ferias', u'Provisão de Férias'),
    ('provisao_decimo_terceiro', u'Provisão de Décimo Terceiro (13º)'),
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
    contract_id_readonly = fields.Many2many(
        comodel_name='hr.contract',
        string='Contratos',
    )
    departamento_id = fields.Many2one(
        comodel_name='hr.department',
        string='Departamento',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Empresa',
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
    def verificar_holerites_gerados(self):
        contract_id = self.env['hr.contract'].search(
            [
                ('company_id', '=', self.company_id.id)
            ]
        )
        contratos = [contrato.id for contrato in contract_id]
        payslip_obj = self.env['hr.payslip']
        payslips = payslip_obj.search(
            [
                ('tipo_de_folha', '=', self.tipo_de_folha),
                ('date_from', '>=', self.date_start),
                ('date_to', '<=', self.date_end),
                ('contract_id', 'in', contratos)
            ]
        )
        contratos_holerites_gerados = []
        for payslip in payslips:
            if payslip.contract_id.id not in contratos_holerites_gerados:
                contratos_holerites_gerados.append(payslip.contract_id.id)
        contratos_sem_holerite = [
            contrato.id for contrato in contract_id
            if contrato.id not in contratos_holerites_gerados
            ]
        if self.id:
            self.write(
                {
                    'contract_id': [(6, 0, contratos_sem_holerite)],
                    'contract_id_readonly': [(6, 0, contratos_sem_holerite)],
                }
            )
        else:
            self.contract_id = contratos_sem_holerite
            self.contract_id_readonly = contratos_sem_holerite

    @api.multi
    def gerar_holerites(self):
        for contrato in self.contract_id:
            try:
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
                payslip._compute_set_employee_id()
                payslip.compute_sheet()
            except:
                self._cr.rollback()
                pass
        self.verificar_holerites_gerados()
