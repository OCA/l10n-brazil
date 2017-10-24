# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from openerp import api, fields, models

MES_DO_ANO = [
    (1, u'Janeiro'),
    (2, u'Fevereiro'),
    (3, u'Março'),
    (4, u'Abril'),
    (5, u'Maio'),
    (6, u'Junho'),
    (7, u'Julho'),
    (8, u'Agosto'),
    (9, u'Setembro'),
    (10, u'Outubro'),
    (11, u'Novembro'),
    (12, u'Dezembro'),
    (13, u'13º Salário')
]

TIPO_DE_FOLHA = [
    ('normal', u'Folha normal'),
    ('adiantamento_13', u'13º Salário - Adiantamento'),
    ('decimo_terceiro', u'13º Salário'),
    ('provisao_ferias', u'Provisão de Férias'),
    ('provisao_decimo_terceiro', u'Provisão de Décimo Terceiro (13º)'),
]


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"
    _order = "ano desc,mes_do_ano desc,tipo_de_folha asc, company_id asc"
    _sql_constraints = [
        ('lote_unico',
         'unique(ano, mes_do_ano, tipo_de_folha, company_id)',
         'Este Lote de Holerite já existe!')
    ]

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
        default=lambda self: self.env.user.company_id or '',
    )

    @api.onchange('tipo_de_folha')
    def fixa_decimo_terceiro(self):
        if self.tipo_de_folha == 'adiantamento_13' and self.mes_do_ano == 12:
            self.tipo_de_folha = 'decimo_terceiro'
            self.mes_do_ano = 13
        else:
            if self.tipo_de_folha == 'decimo_terceiro':
                self.mes_do_ano = 13
            elif self.mes_do_ano == 13:
                self.mes_do_ano = datetime.now().month

    @api.onchange('mes_do_ano', 'ano')
    def buscar_datas_periodo(self):
        if not self.mes_do_ano:
            self.mes_do_ano = datetime.now().month

        if self.tipo_de_folha == 'adiantamento_13' and self.mes_do_ano == 12:
            self.tipo_de_folha = 'decimo_terceiro'
            self.mes_do_ano = 13

        mes = self.mes_do_ano
        if mes > 12:
            mes = 12
            self.tipo_de_folha = 'decimo_terceiro'
        elif self.tipo_de_folha == 'decimo_terceiro':
            self.tipo_de_folha = 'normal'

        ultimo_dia_do_mes = str(
            self.env['resource.calendar'].get_ultimo_dia_mes(
                mes, self.ano))

        primeiro_dia_do_mes = str(
            datetime.strptime(str(mes) + '-' +
                              str(self.ano), '%m-%Y'))

        self.date_start = primeiro_dia_do_mes
        self.date_end = ultimo_dia_do_mes


    @api.multi
    def verificar_holerites_gerados(self):
        for lote in self:
            dominio_contratos = [
                    ('date_start', '<=', lote.date_end),
                    ('company_id', '=', lote.company_id.id),
                ]
            if lote.tipo_de_folha != 'normal':
                dominio_contratos += [
                    ('categoria', 'not in', ['721', '722']),
                ]
            contracts_id = self.env['hr.contract'].search(dominio_contratos)

            payslips = self.env['hr.payslip'].search([
                ('tipo_de_folha', '=', self.tipo_de_folha),
                ('date_from', '>=', self.date_start),
                ('date_to', '<=', self.date_end),
                ('contract_id', 'in', contracts_id.ids)
            ])

            contratos_com_holerites = []
            for payslip in payslips:
                if payslip.contract_id.id not in contratos_com_holerites:
                    contratos_com_holerites.append(payslip.contract_id.id)

            contratos_sem_holerite = [
                contrato.id for contrato in contracts_id
                if (contrato.id not in contratos_com_holerites)
                   and (contrato.date_start <= lote.date_end)
                   and ((contrato.date_end >= lote.date_start)
                   or (not contrato.date_end))]

            lote.write({
                'contract_id': [(6, 0, contratos_sem_holerite)],
                'contract_id_readonly': [(6, 0, contratos_sem_holerite)],
            })

    @api.multi
    def gerar_holerites(self):
        self.verificar_holerites_gerados()
        for contrato in self.contract_id:
            try:
                payslip_obj = self.env['hr.payslip']
                payslip = payslip_obj.create({
                    'contract_id': contrato.id,
                    'mes_do_ano': self.mes_do_ano,
                    'mes_do_ano2': self.mes_do_ano,
                    'ano': self.ano,
                    'employee_id': contrato.employee_id.id,
                    'tipo_de_folha': self.tipo_de_folha,
                    'payslip_run_id': self.id,
                })
                payslip._compute_set_dates()
                payslip.compute_sheet()
            except:
                payslip.unlink()
                continue
        self.verificar_holerites_gerados()

    @api.multi
    def close_payslip_run(self):
        for lote in self:
            for holerite in lote.slip_ids:
                holerite.hr_verify_sheet()
        super(HrPayslipRun, self).close_payslip_run()
