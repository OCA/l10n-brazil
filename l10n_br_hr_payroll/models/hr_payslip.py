# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, fields, models, exceptions, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from lxml import etree

_logger = logging.getLogger(__name__)

try:
    from pybrasil import valor, data
except ImportError:
    _logger.info('Cannot import pybrasil')

MES_DO_ANO = [
    (1, u'Janeiro'),
    (2, u'Fevereiro'),
    (3, u'Marco'),
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
    ('rescisao', u'Rescisão'),
    ('ferias', u'Férias'),
    ('decimo_terceiro', u'Décimo terceiro (13º)'),
    ('aviso_previo', u'Aviso Prévio'),
    ('licenca_maternidade', u'Licença maternidade'),
    ('auxilio_doenca', u'Auxílio doença'),
    ('auxílio_acidente_trabalho', u'Auxílio acidente de trabalho'),
]


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def _buscar_dias_aviso_previo(self):
        for payslip in self:
            if payslip.tipo_de_folha == 'aviso_previo':
                periodos_aquisitivos = self.env['hr.vacation.control'].search(
                    [
                        ('contract_id', '=', payslip.contract_id.id),
                        ('fim_aquisitivo', '<', payslip.date_to)
                    ]
                )
                if periodos_aquisitivos:
                    payslip.dias_aviso_previo = 30 + len(
                        periodos_aquisitivos) * 3
                else:
                    payslip.dias_aviso_previo = 30

    @api.multi
    def _valor_total_folha(self):
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
            codigo = {}
            codigo['BASE_FGTS'] = \
                holerite.env\
                .ref('l10n_br_hr_payroll.hr_salary_rule_BASE_FGTS').code
            codigo['BASE_INSS'] = \
                holerite.env\
                .ref('l10n_br_hr_payroll.hr_salary_rule_BASE_INSS').code
            codigo['BASE_IRPF'] = \
                holerite.env\
                .ref('l10n_br_hr_payroll.hr_salary_rule_BASE_IRPF').code
            codigo['FGTS'] = \
                holerite.env\
                .ref('l10n_br_hr_payroll.hr_salary_rule_FGTS').code
            codigo['INSS'] = \
                holerite.env\
                .ref('l10n_br_hr_payroll.hr_salary_rule_INSS').code
            codigo['IRPF'] = \
                holerite.env\
                .ref('l10n_br_hr_payroll.hr_salary_rule_IRPF').code
            for line in holerite.line_ids:
                total += line.valor_provento - line.valor_deducao
                total_proventos += line.valor_provento
                total_descontos += line.valor_deducao
                if codigo['BASE_FGTS']:
                    base_fgts = line.total
                elif codigo['BASE_INSS']:
                    base_inss = line.total
                elif codigo('BASE_IRPF'):
                    base_irpf = line.total
                elif codigo['FGTS']:
                    fgts = line.total
                elif codigo['INSS']:
                    inss = line.total
                elif codigo['IRPF']:
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
            holerite.data_admissao_fmt =\
                data.formata_data(holerite.contract_id.date_start)
            holerite.salario_base_fmt =\
                valor.formata_valor(holerite.contract_id.wage)
            holerite.total_folha_fmt =\
                valor.formata_valor(holerite.total_folha)
            holerite.total_proventos_fmt =\
                valor.formata_valor(holerite.total_proventos)
            holerite.total_descontos_fmt =\
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
            holerite.data_pagamento = \
                str((fields.Datetime.from_string(holerite.date_from) +
                     relativedelta(days=-2)).date())
            # TO DO Verificar datas de feriados.
            # A biblioteca aceita os parametros de feriados, mas a utilizacao
            # dos feriados é diferente do odoo.
            # Logo o método só é utilizado para antecipar em casos de finais
            # de semana.
            holerite.data_pagamento = data.formata_data(
                data.dia_util_pagamento(
                    data_vencimento=holerite.data_pagamento, antecipa=True,
                )
            )
            holerite.inicio_aquisitivo_fmt = data.formata_data(
                holerite.periodo_aquisitivo.inicio_aquisitivo
            )
            holerite.fim_aquisitivo_fmt = data.formata_data(
                holerite.periodo_aquisitivo.fim_aquisitivo
            )
            holerite.inicio_gozo_fmt = data.formata_data(
                holerite.date_from
            )
            holerite.fim_gozo_fmt = data.formata_data(
                holerite.date_to
            )

    employee_id_readonly = fields.Many2one(
        string=u'Funcionário',
        comodel_name='hr.employee',
        compute='set_employee_id',
    )
    is_simulacao = fields.Boolean(
        string=u"Simulação",
    )
    dias_aviso_previo = fields.Integer(
        string="Dias de Aviso Prévio",
    )

    @api.depends('line_ids')
    @api.model
    def _buscar_payslip_line(self):
        for holerite in self:
            lines = []
            for line in holerite.line_ids:
                if line.valor_provento or line.valor_deducao:
                    lines.append(line.id)
            holerite.line_resume_ids = lines

    tipo_de_folha = fields.Selection(
        selection=TIPO_DE_FOLHA,
        string=u'Tipo de folha',
        default='normal',
    )

    struct_id_readonly = fields.Many2one(
        string=u'Estrutura de Salário',
        comodel_name='hr.payroll.structure',
        compute='set_employee_id',
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

    data_mes_ano = fields.Char(
        string=u'Mês/Ano',
        compute='computar_mes_ano',
    )

    total_folha = fields.Float(
        string=u'Total',
        default=0.00,
        compute='_valor_total_folha'
    )

    total_folha_fmt = fields.Char(
        string=u'Total',
        default='0',
        compute='_valor_total_folha'
    )

    data_admissao_fmt = fields.Char(
        string=u'Data de admissao',
        default='0',
        compute='_valor_total_folha'
    )

    salario_base_fmt = fields.Char(
        string=u'Salario Base',
        default='0',
        compute='_valor_total_folha'
    )

    total_proventos = fields.Float(
        string=u'Total Proventos',
        default=0.00,
        compute='_valor_total_folha'
    )

    total_proventos_fmt = fields.Char(
        string=u'Total Proventos',
        default='0',
        compute='_valor_total_folha'
    )

    total_descontos = fields.Float(
        string=u'Total Descontos',
        default=0.00,
        compute='_valor_total_folha'
    )

    total_descontos_fmt = fields.Char(
        string=u'Total Descontos',
        default='0',
        compute='_valor_total_folha'
    )

    base_fgts = fields.Float(
        string=u'Base do FGTS',
        default=0.00,
        compute='_valor_total_folha'
    )

    base_fgts_fmt = fields.Char(
        string=u'Base do FGTS',
        default='0',
        compute='_valor_total_folha'
    )

    base_inss = fields.Float(
        string=u'Base do INSS',
        default=0.00,
        compute='_valor_total_folha'
    )

    base_inss_fmt = fields.Char(
        string=u'Base do INSS',
        default='0',
        compute='_valor_total_folha'
    )

    base_irpf = fields.Float(
        string=u'Base do IRPF',
        default=0.00,
        compute='_valor_total_folha'
    )

    base_irpf_fmt = fields.Char(
        string=u'Base do IRPF',
        default='0',
        compute='_valor_total_folha'
    )

    fgts = fields.Float(
        string=u'FGTS',
        default=0.00,
        compute='_valor_total_folha'
    )

    fgts_fmt = fields.Char(
        string=u'FGTS',
        default='0',
        compute='_valor_total_folha'
    )

    inss = fields.Float(
        string=u'INSS',
        default=0.00,
        compute='_valor_total_folha'
    )

    inss_fmt = fields.Char(
        string=u'INSS',
        default='0',
        compute='_valor_total_folha'
    )

    irpf = fields.Float(
        string=u'IRPF',
        default=0.00,
        compute='_valor_total_folha'
    )

    irpf_fmt = fields.Char(
        string=u'IRPF',
        default='0',
        compute='_valor_total_folha'
    )

    data_extenso = fields.Char(
        string=u'Data por Extenso',
        compute='_valor_total_folha'
    )

    data_retorno = fields.Char(
        string=u'Data de Retorno',
        compute='_valor_total_folha'
    )

    data_pagamento = fields.Char(
        string=u'Data de Pagamento de férias',
        compute='_valor_total_folha',
    )

    inicio_aquisitivo_fmt = fields.Char(
        string=u'Inicio do Período Aquisitivo Formatado',
        compute='_valor_total_folha',
    )
    fim_aquisitivo_fmt = fields.Char(
        string=u'Fim do Período Aquisitivo Formatado',
        compute='_valor_total_folha',
    )
    inicio_gozo_fmt = fields.Char(
        string=u'Inicio do Período de Gozo Formatado',
        compute='_valor_total_folha',
    )
    fim_gozo_fmt = fields.Char(
        string=u'Fom do Período de Gozo Formatado',
        compute='_valor_total_folha',
    )

    medias_proventos = fields.One2many(
        string=u'Linhas das medias dos proventos',
        comodel_name='l10n_br.hr.medias',
        inverse_name='holerite_id',
    )

    line_resume_ids = fields.One2many(
        comodel_name='hr.payslip.line',
        inverse_name='slip_id',
        compute=_buscar_payslip_line,
        string=u"Holerite Resumo",
    )

    @api.onchange('holidays_ferias')
    def _set_holidays_ferias(self):
        if self.holidays_ferias:
            self.periodo_aquisitivo = self.holidays_ferias.controle_ferias[0]
            self.date_from = self.holidays_ferias.date_from
            self.date_to = self.holidays_ferias.date_to

    holidays_ferias = fields.Many2one(
        comodel_name='hr.holidays',
        string=u'Solicitação de Férias',
        help=u'Período de férias apontado pelo funcionário em '
             u'Pedidos de Férias',
    )

    periodo_aquisitivo = fields.Many2one(
        comodel_name='hr.vacation.control',
        string="Período Aquisitivo",
        domain="[('contract_id','=',contract_id)]",
    )

    @api.depends('periodo_aquisitivo')
    def _set_periodo_aquisitivo_readonly(self):
        for holerite in self:
            holerite.periodo_aquisitivo_readonly = holerite.periodo_aquisitivo

    periodo_aquisitivo_readonly = fields.Many2one(
        comodel_name='hr.vacation.control',
        string="Período Aquisitivo",
        compute='_set_periodo_aquisitivo_readonly',
    )

    @api.depends('periodo_aquisitivo')
    @api.model
    def _get_saldo_periodo_aquisitivo(self):
        for holerite in self:
            if holerite.periodo_aquisitivo:
                holerite.saldo_periodo_aquisitivo = \
                    holerite.periodo_aquisitivo.saldo

    saldo_periodo_aquisitivo = fields.Integer(
        string="Saldo de dias do Periodo Aquisitivo",
        compute='_get_saldo_periodo_aquisitivo',
        help=u'Saldo de dias do funcionaŕio, de acordo com número de faltas'
             u'dentro do período aquisitivo selecionado.',
        store=True,
    )

    def get_attendances(self, nome, sequence, code, number_of_days,
                        number_of_hours, contract_id):
        attendance = {
            'name': nome,
            'sequence': sequence,
            'code': code,
            'number_of_days': number_of_days,
            'number_of_hours': number_of_hours,
            'contract_id': contract_id.id,
        }
        return attendance

    @api.multi
    def unlink(self):
        for payslip in self:
            if not payslip.user_has_groups('base.group_hr_manager'):
                if payslip.state not in ['draft', 'cancel']:
                    raise exceptions.Warning(
                        _('You cannot delete a payslip which is not '
                          'draft or cancelled or permission!')
                    )
            payslip.cancel_sheet()
            return super(HrPayslip, payslip).unlink()

    @api.multi
    def get_worked_day_lines(self, contract_id, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should
        be applied for the given contract between date_from and date_to
        """
        result = []
        for contract_id in self.env['hr.contract'].browse(contract_id):

            # get dias Base para cálculo do mês
            dias_mes = self.env['resource.calendar'].get_dias_base(
                fields.Datetime.from_string(date_from),
                fields.Datetime.from_string(date_to)
            )
            result += [self.get_attendances(u'Dias Base', 1, u'DIAS_BASE',
                                            dias_mes, 0.0, contract_id)]

            # get dias uteis
            dias_uteis = self.env['resource.calendar'].quantidade_dias_uteis(
                fields.Datetime.from_string(date_from),
                fields.Datetime.from_string(date_to),
            )
            result += [self.get_attendances(u'Dias Úteis', 2, u'DIAS_UTEIS',
                                            dias_uteis, 0.0, contract_id)]
            # get faltas
            leaves = {}
            hr_contract = self.env['hr.contract'].browse(contract_id.id)
            leaves = self.env['resource.calendar'].get_ocurrences(
                hr_contract.employee_id.id, date_from, date_to)
            if leaves.get('faltas_nao_remuneradas'):
                qtd_leaves = leaves['quantidade_dias_faltas_nao_remuneradas']
                result += [self.get_attendances(u'Faltas Não remuneradas', 3,
                                                u'FALTAS_NAO_REMUNERADAS',
                                                qtd_leaves,
                                                0.0, contract_id)]
            # get Quantidade de DSR
            quantity_DSR = hr_contract.working_hours. \
                quantidade_de_DSR(date_from, date_to)
            if quantity_DSR:
                result += [self.get_attendances(u'DSR do Mês', 4,
                                                u'DSR_TOTAL', quantity_DSR,
                                                0.0, contract_id)]
            # get discount DSR
            quantity_DSR_discount = self.env['resource.calendar']. \
                get_quantity_discount_DSR(leaves['faltas_nao_remuneradas'],
                                          hr_contract.working_hours.leave_ids,
                                          date_from, date_to)
            if leaves.get('faltas_nao_remuneradas'):
                result += [self.get_attendances(u'DSR a serem descontados', 5,
                                                u'DSR_PARA_DESCONTAR',
                                                quantity_DSR_discount,
                                                0.0, contract_id)]
            # get dias de férias + get dias de abono pecuniario
            quantidade_dias_ferias, quantidade_dias_abono = \
                self.env['resource.calendar'].get_quantidade_dias_ferias(
                    hr_contract.employee_id.id, date_from, date_to)

            result += [
                self.get_attendances(
                    u'Quantidade dias em Férias', 6, u'FERIAS',
                    quantidade_dias_ferias, 0.0, contract_id
                )
            ]

            result += [
                self.get_attendances(
                    u'Quantidade dias Abono Pecuniario', 7,
                    u'ABONO_PECUNIARIO', quantidade_dias_abono,
                    0.0, contract_id
                )
            ]
            # se o periodo aquisitivo ja estiver definido, pega o saldo de dias
            if self.periodo_aquisitivo:
                saldo_ferias = self.periodo_aquisitivo.saldo
                result += [
                    self.get_attendances(
                        u'Saldo de dias máximo para Férias', 8,
                        u'SALDO_FERIAS', saldo_ferias,
                        0.0, contract_id
                    )
                ]

            # get Dias Trabalhados
            quantidade_dias_trabalhados = \
                30 - leaves['quantidade_dias_faltas_nao_remuneradas'] - \
                quantity_DSR_discount - quantidade_dias_ferias
            result += [self.get_attendances(u'Dias Trabalhados', 34,
                                            u'DIAS_TRABALHADOS',
                                            quantidade_dias_trabalhados,
                                            0.0, contract_id)]
        return result

    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        res = super(HrPayslip, self).get_inputs(
            contract_ids, date_from, date_to
        )
        contract = self.env['hr.contract'].browse(contract_ids)
        salario_mes_dic = {
            'name': 'Salário Mês',
            'code': 'SALARIO_MES',
            'amount': contract._salario_mes(date_from, date_to),
            'contract_id': contract.id,
        }
        salario_dia_dic = {
            'name': 'Salário Dia',
            'code': 'SALARIO_DIA',
            'amount': contract._salario_dia(date_from, date_to),
            'contract_id': contract.id,
        }
        salario_hora_dic = {
            'name': 'Salário Hora',
            'code': 'SALARIO_HORA',
            'amount': contract._salario_hora(date_from, date_to),
            'contract_id': contract.id,
        }
        res += [salario_mes_dic]
        res += [salario_dia_dic]
        res += [salario_hora_dic]
        return res

    def INSS(self, BASE_INSS):
        tabela_inss_obj = self.env['l10n_br.hr.social.security.tax']
        inss = tabela_inss_obj._compute_inss(BASE_INSS, self.date_from)
        return inss

    def IRRF(self, BASE_IR, BASE_INSS):
        tabela_irrf_obj = self.env['l10n_br.hr.income.tax']
        inss = self.INSS(BASE_INSS)
        irrf = tabela_irrf_obj._compute_irrf(
            BASE_IR, self.employee_id.id, inss, self.date_from
        )
        return irrf

    @api.model
    def get_contract_specific_rubrics(self, contract_id, rule_ids):
        contract = self.env['hr.contract'].browse(contract_id.id)
        for rule in contract.specific_rule_ids:
            if self.date_from >= rule.date_start:
                if not rule.date_stop or self.date_to <= rule.date_stop:
                    rule_ids.append((rule.rule_id.id, rule.rule_id.sequence))
        return rule_ids

    @api.model
    def get_specific_rubric_value(self, rubrica_id, medias_obj=False):
        for rubrica in self.contract_id.specific_rule_ids:
            if rubrica.rule_id.id == rubrica_id:
                if medias_obj:
                    if rubrica.rule_id.code not in medias_obj.dict.keys():
                        return 0
                return rubrica.specific_quantity * \
                    rubrica.specific_percentual/100 * \
                    rubrica.specific_amount

    @api.multi
    def _buscar_valor_salario(self, codigo):
        for tipo_salario in self.input_line_ids:
            if tipo_salario.code == codigo:
                return tipo_salario.amount
        return 0.00

    @api.multi
    def _get_rat_fap_period_values(self, year):
        rat_fap_obj = self.env['l10n_br.hr.rat.fap']
        rat_fap = rat_fap_obj = rat_fap_obj.search(
            [('year', '=', year), ('company_id', '=', self.company_id.id)]
        )
        if rat_fap:
            return rat_fap
        else:
            raise exceptions.Warning(
                _('Can\'t find this year values in Rat Fap Table')
            )

    @api.multi
    def buscar_estruturas_salario(self):
        if self.tipo_de_folha == "normal" \
                or self.tipo_de_folha == "aviso_previo":
            return self.contract_id.struct_id
        elif self.tipo_de_folha == "decimo_terceiro":
            if self.mes_do_ano < 12:
                estrutura_decimo_terceiro = self.env.ref(
                    'l10n_br_hr_payroll.'
                    'hr_salary_structure_PRIMEIRA_PARCELA_13'
                )
                return estrutura_decimo_terceiro
            else:
                estrutura_decimo_terceiro = self.env.ref(
                    'l10n_br_hr_payroll.'
                    'hr_salary_structure_SEGUNDA_PARCELA_13'
                )
                return estrutura_decimo_terceiro
        elif self.tipo_de_folha == "ferias":
            estrutura_decimo_terceiro = self.env.ref(
                'l10n_br_hr_payroll.'
                'hr_salary_structure_FERIAS'
            )
            return estrutura_decimo_terceiro

    # @api.multi
    # def buscar_media_rubrica(self, rubrica_id):
    #     rubrica = self.env['hr.salary.rule'].browse(rubrica_id)
    #     for media in self.medias_proventos:
    #         if rubrica.name == media.nome_rubrica:
    #             return media.media

    @api.multi
    def BUSCAR_PRIMEIRA_PARCELA(self):
        primeira_parcela_struct_id = self.env.ref(
            'l10n_br_hr_payroll.hr_salary_structure_PRIMEIRA_PARCELA_13'
        )
        primeira_parcela_id = self.env.ref(
            'l10n_br_hr_payroll.hr_salary_rule_PRIMEIRA_PARCELA_13'
        )
        payslip_id = self.env['hr.payslip'].search(
            [
                ('contract_id', '=', self.contract_id.id),
                ('date_from', '>=', str(self.ano) + '-01-01'),
                ('date_to', '<=', str(self.ano) + '-11-30'),
                ('struct_id', '=', primeira_parcela_struct_id.id)
            ]
        )
        if len(payslip_id) > 1:
            raise exceptions.Warning(
                _('Existe mais de um holerite da primeira parcela do 13º!')
            )
        for line in payslip_id.line_ids:
            if line.salary_rule_id.id == primeira_parcela_id.id:
                return line.total

    @api.multi
    def get_payslip_lines(self, payslip_id):
        """
        get_payslip_lines(cr, uid, contract_ids, payslip.id, context=context)]
        Na chamada da função o contract_ids é passado como active_ids (ids) e
         o id fo payslip é passado no parâmettro do payslip
        :param payslip_id: Id do payslip corrente
                self : Id do contract
        :return:
        """
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(
                    localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = \
                category.code in localdict['categories'].dict and \
                localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict):
                self.employee_id = employee_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code,
            mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                self.env.cr.execute(
                    "SELECT sum(amount) as sum "
                    "FROM hr_payslip as hp, hr_payslip_input as pi "
                    "WHERE hp.employee_id = %s AND hp.state = 'done' "
                    "AND hp.date_from >= %s AND hp.date_to <= %s "
                    "AND hp.id = pi.payslip_id AND pi.code = %s",
                    (self.employee_id, from_date, to_date, code))
                res = self.env.cr.fetchone()[0]
                return res or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly
            for usability purposes"""
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                self.env.cr.execute(
                    "SELECT sum(number_of_days) as number_of_days, "
                    "sum(number_of_hours) as number_of_hours "
                    "FROM hr_payslip as hp, hr_payslip_worked_days as pi "
                    "WHERE hp.employee_id = %s AND hp.state = 'done' "
                    "AND hp.date_from >= %s AND hp.date_to <= %s "
                    "AND hp.id = pi.payslip_id AND pi.code = %s",
                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code,
            mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                self.env.cr.execute(
                    "SELECT sum(case when hp.credit_note = False "
                    "then (pl.total) else (-pl.total) end) "
                    "FROM hr_payslip as hp, hr_payslip_line as pl "
                    "WHERE hp.employee_id = %s AND hp.state = 'done' "
                    "AND hp.date_from >= %s AND hp.date_to <= %s "
                    "AND hp.id = pl.slip_id AND pl.code = %s",
                    (self.employee_id, from_date, to_date, code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        # we keep a dict with the result because a value can be overwritten
        # by another rule with the same code
        result_dict = {}
        rules = {}
        categories_dict = {}
        blacklist = []
        payslip_obj = self.env['hr.payslip']
        obj_rule = self.env['hr.salary.rule']
        payslip = payslip_obj.browse(payslip_id)
        worked_days = {}
        for worked_days_line in payslip.worked_days_line_ids:
            if payslip.tipo_de_folha == "aviso_previo" \
                    and worked_days_line.code == u'DIAS_TRABALHADOS':
                worked_days_line.number_of_days = payslip.dias_aviso_previo
                worked_days[worked_days_line.code] = worked_days_line
            else:
                worked_days[worked_days_line.code] = worked_days_line
        inputs = {}
        for input_line in payslip.input_line_ids:
            inputs[input_line.code] = input_line
        medias = {}
        for media in payslip.medias_proventos:
            medias[media.rubrica_id.code] = media
        input_obj = InputLine(payslip.employee_id.id, inputs)
        worked_days_obj = WorkedDays(payslip.employee_id.id, worked_days)
        payslip_obj = Payslips(payslip.employee_id.id, payslip)
        rules_obj = BrowsableObject(payslip.employee_id.id, rules)
        medias_obj = BrowsableObject(payslip.employee_id.id, medias) \
            if payslip.tipo_de_folha in ["ferias", "decimo_terceiro"] \
            else False
        categories_obj = \
            BrowsableObject(payslip.employee_id.id, categories_dict)

        salario_mes = payslip._buscar_valor_salario('SALARIO_MES')
        salario_dia = payslip._buscar_valor_salario('SALARIO_DIA')
        salario_hora = payslip._buscar_valor_salario('SALARIO_HORA')
        rat_fap = payslip._get_rat_fap_period_values(payslip.ano)
        baselocaldict = {
            'CALCULAR': payslip, 'BASE_INSS': 0.0, 'BASE_FGTS': 0.0,
            'BASE_IR': 0.0, 'categories': categories_obj, 'rules': rules_obj,
            'payslip': payslip_obj, 'worked_days': worked_days_obj,
            'inputs': input_obj, 'rubrica': None, 'SALARIO_MES': salario_mes,
            'SALARIO_DIA': salario_dia, 'SALARIO_HORA': salario_hora,
            'RAT_FAP': rat_fap, 'MEDIAS': medias_obj,
        }

        for contract_ids in self:
            # get the ids of the structures on the contracts
            # and their parent id as well
            # structure_ids = self.env['hr.contract'].browse(
            #     contract_ids.ids).get_all_structures()
            structure_ids = payslip.struct_id._get_parent_structure()

            # get the rules of the structure and thier children
            rule_ids = self.env['hr.payroll.structure'].browse(
                structure_ids).get_all_rules()
            rule_ids = payslip.get_contract_specific_rubrics(
                contract_ids, rule_ids)

            # run the rules by sequence
            sorted_rule_ids = \
                [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]

            for contract in self.env['hr.contract'].browse(contract_ids.ids):
                employee = contract.employee_id
                localdict = dict(
                    baselocaldict, employee=employee, contract=contract)
                for rule in obj_rule.browse(sorted_rule_ids):
                    key = rule.code + '-' + str(contract.id)
                    localdict['result'] = None
                    localdict['result_qty'] = 1.0
                    localdict['result_rate'] = 100
                    localdict['rubrica'] = rule
                    # check if the rule can be applied
                    if obj_rule.satisfy_condition(rule.id, localdict) \
                            and rule.id not in blacklist:
                        # compute the amount of the rule
                        amount, qty, rate = \
                            obj_rule.compute_rule(rule.id, localdict)
                        # se ja tiver sido calculado a media dessa rubrica,
                        # utilizar valor da media e multiplicar pela reinciden.
                        if medias.get(rule.code):
                            amount = medias.get(rule.code).media/12
                            qty = medias.get(rule.code).meses

                        # check if there is already a rule computed
                        # with that code
                        previous_amount = \
                            rule.code in localdict and \
                            localdict[rule.code] or 0.0
                        # set/overwrite the amount computed
                        # for this rule in the localdict
                        tot_rule = amount * qty * rate / 100.0
                        localdict[rule.code] = tot_rule
                        rules[rule.code] = rule
                        if rule.compoe_base_INSS:
                            localdict['BASE_INSS'] += tot_rule
                        if rule.compoe_base_IR:
                            localdict['BASE_IR'] += tot_rule
                        if rule.compoe_base_FGTS:
                            localdict['BASE_FGTS'] += tot_rule
                        # sum the amount for its salary category
                        localdict = _sum_salary_rule_category(
                            localdict, rule.category_id,
                            tot_rule - previous_amount)
                        # create/overwrite the rule in the temporary results
                        result_dict[key] = {
                            'salary_rule_id': rule.id,
                            'contract_id': contract.id,
                            'name': u'Média de ' + rule.name
                            if medias_obj else rule.name,
                            'code': rule.code,
                            'category_id': rule.category_id.id,
                            'sequence': rule.sequence,
                            'appears_on_payslip': rule.appears_on_payslip,
                            'condition_select': rule.condition_select,
                            'condition_python': rule.condition_python,
                            'condition_range': rule.condition_range,
                            'condition_range_min': rule.condition_range_min,
                            'condition_range_max': rule.condition_range_max,
                            'amount_select': rule.amount_select,
                            'amount_fix': rule.amount_fix,
                            'amount_python_compute':
                                rule.amount_python_compute,
                            'amount_percentage': rule.amount_percentage,
                            'amount_percentage_base':
                                rule.amount_percentage_base,
                            'register_id': rule.register_id.id,
                            'amount': amount,
                            'employee_id': contract.employee_id.id,
                            'quantity': qty,
                            'rate': rate,
                        }
                    else:
                        rules_seq = rule._model._recursive_search_of_rules(
                            self._cr, self._uid, rule, self._context)
                        blacklist += [id for id, seq in rules_seq]

            result = [value for code, value in result_dict.items()]
            return result

    def atualizar_worked_days_inputs(self):
        """
        Atualizar os campos worked_days_line_ids e input_line_ids do holerite.
        Com os campos de contrato, employee, date_from e date_to do holerite
        ja setados, esse metodo exclui as variaveis base para calculo do
        holerite e os instancia novamente atualizando os valore.
        :return: Campos atualizados
        """
        hr_payslip_worked_days_obj = self.env['hr.payslip.worked_days']
        hr_payslip_input_obj = self.env['hr.payslip.input']

        for holerite in self:
            # delete old worked days lines
            if holerite.worked_days_line_ids:
                for worked_day_id in holerite.worked_days_line_ids:
                    worked_day_id.unlink()
            # get dict com valores do worked_days_lines
            worked_days_line_ids = self.get_worked_day_lines(
                holerite.contract_id.id, holerite.date_from, holerite.date_to
            )
            # Atrelar o worked_days a payslip atual e instanciar o objeto
            for wd_line in worked_days_line_ids:
                wd_line['payslip_id'] = self.id
                hr_payslip_worked_days_obj.create(wd_line)

            # delete old input lines
            if holerite.input_line_ids:
                for input_id in holerite.input_line_ids:
                    input_id.unlink()
            # get dict com valores do Inputs_lines
            input_line_ids = self.get_inputs(
                holerite.contract_id.id, holerite.date_from, holerite.date_to
            )
            # Atrelar o Inputs_line a payslip atual e instanciar o objeto
            for input_line in input_line_ids:
                input_line['payslip_id'] = self.id
                hr_payslip_input_obj.create(input_line)

    @api.multi
    def onchange_employee_id(self, date_from, date_to, contract_id):
        worked_days_obj = self.env['hr.payslip.worked_days']
        input_obj = self.env['hr.payslip.input']

        # delete old worked days lines
        old_worked_days_ids = worked_days_obj.search(
            [('payslip_id', '=', self.id)]
        )
        if old_worked_days_ids:
            for worked_day_id in old_worked_days_ids:
                worked_day_id.unlink()

        # delete old input lines
        old_input_ids = input_obj.search([('payslip_id', '=', self.id)])
        if old_input_ids:
            for input_id in old_input_ids:
                input_id.unlink()

        # defaults
        res = {
            'value': {
                'line_ids': [],
                'input_line_ids': [],
                'worked_days_line_ids': [],
                'name': '',
            }
        }
        # computation of the salary input
        worked_days_line_ids = self.get_worked_day_lines(
            contract_id, date_from, date_to
        )
        input_line_ids = self.get_inputs(contract_id, date_from, date_to)
        res['value'].update(
            {
                'worked_days_line_ids': worked_days_line_ids,
                'input_line_ids': input_line_ids,
            }
        )
        return res

    @api.multi
    @api.onchange('contract_id')
    def set_employee_id(self):
        for record in self:
            record.struct_id = record.buscar_estruturas_salario()
            record.struct_id_readonly = record.struct_id
            record.set_dates()
            if record.contract_id:
                record.employee_id = record.contract_id.employee_id
                record.employee_id_readonly = record.employee_id

    @api.multi
    @api.onchange('mes_do_ano', 'ano')
    def buscar_datas_periodo(self):
        for record in self:
            record.set_dates()

    def computar_mes_ano(self):
        for record in self:
            record.data_mes_ano = MES_DO_ANO[record.mes_do_ano-1][1][:3] + \
                '/' + str(record.ano)

    def set_dates(self):
        for record in self:
            ultimo_dia_do_mes = str(
                self.env['resource.calendar'].get_ultimo_dia_mes(
                    record.mes_do_ano, record.ano))

            primeiro_dia_do_mes = str(
                datetime.strptime(str(record.mes_do_ano) + '-' +
                                  str(record.ano), '%m-%Y'))

            record.date_from = primeiro_dia_do_mes
            record.date_to = ultimo_dia_do_mes

            data_de_inicio = record.contract_id.date_start
            data_final = record.contract_id.date_end

            if data_de_inicio and primeiro_dia_do_mes < data_de_inicio:
                record.date_from = record.contract_id.date_start

            if data_final and ultimo_dia_do_mes > data_final:
                record.date_to = record.contract_id.date_end

    @api.multi
    def compute_sheet(self):
        if self.tipo_de_folha in ["decimo_terceiro", "ferias", "aviso_previo"]:
            hr_medias_ids, data_de_inicio, data_final = \
                self.gerar_media_dos_proventos()

            # Metodo pra validar se ja foram processadors todos os holerites
            #  usados no calculo das medias
            self.validacao_holerites_anteriores(
                data_de_inicio, data_final, self.contract_id)

            if self.tipo_de_folha == 'ferias':
                if not self.holidays_ferias:
                    raise exceptions.Warning(
                        _('Nenhum Pedido de Ferias encontrado!')
                    )
                if self.holidays_ferias.number_of_days_temp > \
                        self.saldo_periodo_aquisitivo:
                    raise exceptions.Warning(
                        _('Selecionado mais dias de ferias do que o saldo do '
                          'periodo aquisitivo selecionado!')
                    )

                # Atualizar o controle de férias com informacao de quantos dias
                # o funcionario gozara
                self.periodo_aquisitivo.dias_gozados += \
                    self.holidays_ferias.number_of_days_temp

                # Caso o funcionario opte por dividir as férias em dois
                # períodos, e ainda tenha saldo para tal, uma nova linha de
                # controle de féria é criada com base na linha atual
                if self.periodo_aquisitivo.saldo > 0:
                    novo_controle_ferias = self.periodo_aquisitivo.copy()
                    novas_datas = novo_controle_ferias.\
                        calcular_datas_aquisitivo_concessivo(
                            novo_controle_ferias.inicio_aquisitivo
                        )
                    novo_controle_ferias.write(novas_datas)

                # Atualizar o controle de férias com informacoes dos dias
                # gozados pelo funcionario de acordo com a payslip de férias
                self.periodo_aquisitivo.inicio_gozo = \
                    self.holidays_ferias.date_from
                self.periodo_aquisitivo.fim_gozo = \
                    self.holidays_ferias.date_to

            self.atualizar_worked_days_inputs()
        super(HrPayslip, self).compute_sheet()
        self._valor_total_folha()
        return True

    def validacao_holerites_anteriores(self, data_inicio, data_fim, contrato):
        """
        VAlida se existe todos os holerites calculados e confirmados em
        determinado período.
        :param date_from:
        :param date_to:
        :return:
        """
        folha_obj = self.env['hr.payslip']
        data_inicio = fields.Date.from_string(data_inicio).strftime('%Y-%m-01')
        domain = [
            ('date_from', '>=', data_inicio),
            ('date_from', '<=', data_fim),
            ('contract_id', '=', contrato.id),
            ('state', '=', 'done'),
        ]
        folhas_periodo = folha_obj.search(domain)

        folhas_sorted = folhas_periodo.sorted(key=lambda r: r.date_from)
        mes = fields.Date.from_string(data_inicio) + relativedelta(months=-1)

        mes_anterior = ''
        for folha in folhas_sorted:
            if mes_anterior and mes_anterior == folha.mes_do_ano:
                continue
            mes_anterior = folha.mes_do_ano
            mes = mes + relativedelta(months=1)
            if folha.mes_do_ano != mes.month:
                raise exceptions.ValidationError(
                    _("Faltando Holerite confirmado do mês de %s de %s") %
                    (MES_DO_ANO[mes.month-1][1], mes.year))
        mes_final = fields.Date.from_string(data_fim)
        if mes.month != mes_final.month:
            raise exceptions.ValidationError(
                _("Não foi encontrado o último holerite do periodo "
                  "aquisitivo, \nreferente ao mês  de %s de %s") %
                (MES_DO_ANO[mes_final.month-1][1], mes_final.year))

    @api.multi
    def gerar_media_dos_proventos(self):
        medias_obj = self.env['l10n_br.hr.medias']
        if self.tipo_de_folha == 'ferias' \
                or self.tipo_de_folha == 'aviso_previo':
            periodo_aquisitivo = self.periodo_aquisitivo
            data_de_inicio = str(fields.Date.from_string(
                periodo_aquisitivo.inicio_aquisitivo))
            data_final = str(fields.Date.from_string(
                periodo_aquisitivo.fim_aquisitivo))
        elif self.tipo_de_folha == 'decimo_terceiro':
            if self.contract_id.date_start > str(self.ano) + '-01-01':
                data_de_inicio = self.contract_id.date_start
            else:
                data_de_inicio = str(self.ano) + '-01-01'
            data_final = self.date_to
        hr_medias_ids = medias_obj.gerar_media_dos_proventos(
            data_de_inicio, data_final, self)
        return hr_medias_ids, data_de_inicio, data_final

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(HrPayslip, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu
        )
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
