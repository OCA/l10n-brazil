# -*- coding: utf-8 -*-
# Copyright (C) 2018 ABGF (http://www.abgf.gov.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta


from lxml import etree
from openerp import api, fields, models, exceptions, _

_logger = logging.getLogger(__name__)

try:
    from pybrasil import valor, data
    from pybrasil.data import ultimo_dia_mes
    from pybrasil.valor.decimal import Decimal

except ImportError:
    _logger.info('Cannot import pybrasil')

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
]

TIPO_DE_FOLHA = [
    ('normal', u'Folha normal'),
    ('rpa', u'Recibo de Pagamento a Autonômo'),
    ('rescisao', u'Rescisão'),
    ('ferias', u'Férias'),
    ('decimo_terceiro', u'Décimo terceiro (13º)'),
    ('aviso_previo', u'Aviso Prévio'),
    ('provisao_ferias', u'Provisão de Férias'),
    ('provisao_decimo_terceiro', u'Provisão de Décimo terceiro (13º)'),
    ('licenca_maternidade', u'Licença maternidade'),
    ('auxilio_doenca', u'Auxílio doença'),
    ('auxílio_acidente_trabalho', u'Auxílio acidente de trabalho'),
]


class HrPayslipAutonomo(models.Model):
    _name = 'hr.payslip.autonomo'
    _order = 'ano desc, mes_do_ano desc, company_id asc, employee_id asc'

    contract_id = fields.Many2one(
        comodel_name = 'hr.contract',
        string= 'Contrato',
        ondelete='cascade',
        index=True,
        domain="[('tipo','=','autonomo')]",
    )

    employee_id = fields.Many2one(
        string=u'Funcionário',
        comodel_name='hr.employee',
        compute='_compute_set_employee_id',
        store=True,
        required=False,
        states={'draft': [('readonly', False)]}
    )

    state = fields.Selection(
        selection = [
            ('draft', 'Draft'),
            ('verify', 'Waiting'),
            ('done', 'Done'),
            ('cancel', 'Rejected'),
        ],
        default='draft',
        string = 'Status',
        copy=False,
    )

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

    date_from = fields.Date(
        string='Date From',
        #readonly=True,
        #states={'draft': [('readonly', False)]},
        required=True,
        #compute='_compute_set_dates',
        #store=True,
    )

    date_to = fields.Date(
        string='Date To',
        #readonly=True,
        #states={'draft': [('readonly', False)]},
        required=True,
        #compute='_compute_set_dates',
        #store=True,
    )

    struct_id = fields.Many2one(
        string=u'Estrutura de Salário',
        comodel_name='hr.payroll.structure',
        compute='_compute_set_employee_id',
        states={'draft': [('readonly', False)]},
        help=u'Defines the rules that have to be applied to this payslip, '
             u'accordingly to the contract chosen. If you let empty the field '
             u'contract, this field isn\'t mandatory anymore and thus the '
             u'rules applied will be all the rules set on the structure of all'
             u' contracts of the employee valid for the chosen period'
    )

    line_ids = fields.One2many(
        string=u"Holerite Resumo",
        comodel_name='hr.payslip.line',
        inverse_name='slip_autonomo_id',
    )

    line_resume_ids = fields.One2many(
        comodel_name='hr.payslip.line',
        inverse_name='slip_autonomo_id',
        compute='_buscar_payslip_line',
        string=u"Holerite Resumo",
    )

    is_simulacao = fields.Boolean(
        string=u"Simulação",
    )

    tipo_de_folha = fields.Selection(
        selection=TIPO_DE_FOLHA,
        string=u'Tipo de folha',
        default='normal',
    )

    data_mes_ano = fields.Char(
        string=u'Mês/Ano',
        compute='_compute_data_mes_ano',
    )

    total_folha = fields.Float(
        string=u'Total',
        default=0.00,
        compute='_compute_valor_total_folha'
    )

    total_folha_fmt = fields.Char(
        string=u'Total',
        default='0',
        compute='_compute_valor_total_folha'
    )


    salario_base_fmt = fields.Char(
        string=u'Salario Base',
        default='0',
        compute='_compute_valor_total_folha'
    )

    data_extenso = fields.Char(
        string=u'Data por Extenso',
        compute='_compute_valor_total_folha'
    )

    company_id = fields.Many2one(
        string="Empresa",
        comodel_name="res.company",
        related='contract_id.company_id',
        store=True
    )

    total_proventos = fields.Float(
        string=u'Total Proventos',
        default=0.00,
        compute='_compute_valor_total_folha'
    )

    total_proventos_fmt = fields.Char(
        string=u'Total Proventos',
        default='0',
        compute='_compute_valor_total_folha'
    )

    total_descontos = fields.Float(
        string=u'Total Descontos',
        default=0.00,
        compute='_compute_valor_total_folha'
    )

    total_descontos_fmt = fields.Char(
        string=u'Total Descontos',
        default='0',
        compute='_compute_valor_total_folha'
    )

    data_pagamento_autonomo = fields.Date(
        string=u'Data de Pagamento',
    )

    @api.multi
    def _compute_valor_total_folha(self):
        for holerite in self:
            total = 0.00
            total_proventos = 0.00
            total_descontos = 0.00
            base_inss = 0.00
            base_irpf = 0.00
            base_fgts = 0.00
            fgts = 0.00
            inss = 0.00
            irpf = 0.00
            #            codigo = {}
            #            codigo['BASE_FGTS'] = \
            #                holerite.env\
            #                .ref('l10n_br_hr_payroll.hr_salary_rule_BASE_FGTS').code
            #            codigo['BASE_INSS'] = \
            #                holerite.env\
            #                .ref('l10n_br_hr_payroll.hr_salary_rule_BASE_INSS').code
            #            codigo['BASE_IRPF'] = \
            #                holerite.env\
            #                .ref('l10n_br_hr_payroll.hr_salary_rule_BASE_IRPF').code
            #            codigo['FGTS'] = \
            #                holerite.env\
            #                .ref('l10n_br_hr_payroll.hr_salary_rule_FGTS').code
            #            codigo['INSS'] = \
            #                holerite.env\
            #                .ref('l10n_br_hr_payroll.hr_salary_rule_INSS').code
            #            codigo['IRPF'] = \
            #                holerite.env\
            #                .ref('l10n_br_hr_payroll.hr_salary_rule_IRPF').code
            for line in holerite.line_ids:
                total += line.valor_provento - line.valor_deducao
                total_proventos += line.valor_provento
                total_descontos += line.valor_deducao
                if line.code in ['BASE_FGTS', 'BASE_FGTS_13']:
                    base_fgts += line.total
                elif line.code in ['BASE_INSS', 'BASE_INSS_13']:
                    base_inss += line.total
                elif line.code == 'BASE_IRPF':
                    base_irpf = line.total
                elif line.code == 'FGTS':
                    fgts = line.total
                elif line.code == 'INSS':
                    inss = line.total
                elif line.code == 'IRPF':
                    irpf = line.total
            holerite.total_folha = total
            holerite.total_proventos = total_proventos
            holerite.total_descontos = total_descontos
            holerite.base_fgts = base_fgts
            holerite.base_inss = base_inss
            holerite.base_irpf = base_irpf
            holerite.fgts = fgts
            holerite.inss = inss
            holerite.irpf = irpf
            # Formato
            holerite.data_admissao_fmt = \
                data.formata_data(holerite.contract_id.date_start)
            holerite.salario_base_fmt = \
                valor.formata_valor(holerite.contract_id.wage)
            holerite.total_folha_fmt = \
                valor.formata_valor(holerite.total_folha)
            holerite.total_proventos_fmt = \
                valor.formata_valor(holerite.total_proventos)
            holerite.total_descontos_fmt = \
                valor.formata_valor(holerite.total_descontos)
            holerite.base_fgts_fmt = valor.formata_valor(holerite.base_fgts)
            holerite.base_inss_fmt = valor.formata_valor(holerite.base_inss)
            holerite.base_irpf_fmt = valor.formata_valor(holerite.base_irpf)
            holerite.fgts_fmt = valor.formata_valor(holerite.fgts)
            holerite.inss_fmt = valor.formata_valor(holerite.inss)
            holerite.irpf_fmt = valor.formata_valor(holerite.irpf)
            holerite.data_extenso = data.data_por_extenso(fields.Date.today())
            holerite.data_retorno = data.formata_data(
                str((fields.Datetime.from_string(holerite.date_to) +
                     relativedelta(days=1)).date()))

            # holerite.data_pagamento = str(
            #     self.compute_payment_day(holerite.date_from))

            # TO DO Verificar datas de feriados.
            # A biblioteca aceita os parametros de feriados, mas a utilizacao
            # dos feriados é diferente do odoo.
            # Logo o método só é utilizado para antecipar em casos de finais
            # de semana.
            # holerite.data_pagamento = data.formata_data(
            #     data.dia_util_pagamento(
            #         data_vencimento=holerite.data_pagamento, antecipa=True,
            #     )
            # )

    #
    #  Métodos da payslip do autonomo
    #
    @api.multi
    def _compute_data_mes_ano(self):
        for record in self:
            record.data_mes_ano = MES_DO_ANO[record.mes_do_ano - 1][1][:3] + \
                '/' + str(record.ano)

    @api.multi
    def button_hr_validate_payslip_autonomo(self):
        """

        :return:
        """
        for record in self:
            record._buscar_payslip_line()
            record.state = 'done'

    @api.multi
    def unlink(self):
        for payslip in self:
            if payslip.state not in ['draft', 'cancel']:
                raise exceptions.Warning(
                    _('You cannot delete a payslip which is not '
                      'draft or cancelled or permission!')
                )
            payslip.cancel_sheet()
        return super(HrPayslipAutonomo, self).unlink()

    @api.multi
    @api.depends('contract_id', 'mes_do_ano')
    def _compute_set_employee_id(self):
        for record in self:
            if record.contract_id:
                record.employee_id = record.contract_id.employee_id

    @api.multi
    @api.depends('line_ids')
    def _buscar_payslip_line(self):
        for holerite in self:
            lines = []
            for line in holerite.line_ids:
                if line.valor_provento or line.valor_deducao:
                    lines.append(line.id)
            holerite.line_resume_ids = lines

    @api.model
    def _compute_sheet_autonomo(self):
        for holerite in self:
            holerite._buscar_payslip_line()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(HrPayslipAutonomo, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)

        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for sheet in doc.xpath("//sheet"):
                parent = sheet.getparent()
                index = parent.index(sheet)
                for child in sheet:
                    parent.insert(index, child)
                    index += 1
                parent.remove(sheet)
            res['arch'] = etree.tostring(doc)
        return res
