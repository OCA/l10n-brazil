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
        default=lambda self: self.env.user.company_id or '',
    )

    @api.onchange('mes_do_ano', 'ano')
    def buscar_datas_periodo(self):
        ultimo_dia_do_mes = str(
            self.env['resource.calendar'].get_ultimo_dia_mes(
                self.mes_do_ano, self.ano))

        primeiro_dia_do_mes = str(
            datetime.strptime(str(self.mes_do_ano) + '-' +
                              str(self.ano), '%m-%Y'))

        self.date_start = primeiro_dia_do_mes
        self.date_end = ultimo_dia_do_mes

    @api.multi
    def verificar_holerites_gerados(self):
        for lote in self:
            contracts_id = self.env['hr.contract'].search([
                ('date_start', '<', lote.date_end),
                ('company_id', '=', lote.company_id.id)
            ])

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
                if contrato.id not in contratos_com_holerites]

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
