# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from calendar import monthrange
from datetime import datetime, timedelta
import random

from collections import defaultdict

from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY
from lxml import etree
from openerp import api, fields, models, exceptions, _
from openerp.tools import float_compare
from mako.template import Template

from .profiling import (
    clear_prof_data,
    log_prof_data,
    profile
)

from openerp.addons.l10n_br_hr_payroll.constantes import (
    CALCULATED_SPECIFC_RULE,
    MES_DO_ANO,
    MES_DO_ANO2,
    TIPO_DE_FOLHA
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil import valor, data
    from pybrasil.data import ultimo_dia_mes
    from pybrasil.valor.decimal import Decimal

except ImportError:
    _logger.info('Cannot import pybrasil')


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _order = 'ano desc, mes_do_ano desc, tipo_de_folha asc' + \
             ', company_id asc, employee_id asc, number desc'
    _sql_constraints = [
        ('holerite_unico',
         'unique(contract_id, tipo_de_folha, date_from, date_to, is_simulacao, periodo_aquisitivo)',
         'Este Holerite já existe!')
    ]

    @api.multi
    def hr_verify_sheet(self):
        for holerite in self:
            if holerite.state == 'draft':
                holerite.write({'state': 'verify'})

                # Atualizar o controle de férias, o controle de férias do
                # contrato é baseado nos holerites validados
                if holerite.tipo_de_folha in ['rescisao_complementar']:
                    pass
                elif holerite.tipo_de_folha in ['rescisao']:
                    holerite.sudo().contract_id.action_button_update_controle_ferias()
                else:
                    holerite.contract_id.action_button_update_controle_ferias()

                # Validação para confirmação
                liquido = holerite.line_ids.filtered(
                    lambda x: x.code == 'LIQUIDO').total
                if liquido and float_compare(
                        holerite.total_folha, liquido, precision_digits=2):
                    raise exceptions.Warning(
                        _('Rúbrica LIQUIDO com valor inválido!'))

                if holerite.tipo_de_folha == 'rescisao':
                    holerite.contract_id.resignation_cause_id = \
                        holerite.mtv_deslig_esocial
                    holerite.contract_id.resignation_date = \
                        holerite.data_afastamento

                    department_id = self.env['hr.department'].search([
                        ('state','=','ativo'),
                        ('manager_id','=', holerite.employee_id.id),
                    ])

                    validacoes = ''

                    if department_id:
                        validacoes += \
                            _('Funcionário como Gestor do(s) departamento(s):'
                              '\n{}. \nDefinir novo gestor antes de finalizar '
                              'procedimento. \n\n'.format(
                                '\n'.join(department_id.mapped('name'))))

                    holidays_ids = self.env['hr.holidays'].search([
                        ('state','=','confirm'),
                        ('type','=','remove'),
                        ('employee_id','=',holerite.employee_id.id),
                    ])

                    if holidays_ids:
                        validacoes += _('Evento pendente:\n {} \n\n'
                              .format('\n'.join(holidays_ids.mapped('name'))))

                    ligacoes_ids = self.env['hr.telefonia.line'].search([
                        ('state','=','open'),
                        ('employee_id','=',holerite.employee_id.id),
                    ])

                    if ligacoes_ids:
                        validacoes += \
                            _('Ligação em aberto. Atestar ligações nos '
                              'seguintes ramais:\n {} \n\n'.format(
                                ' - '.join(ligacoes_ids.mapped('ramal.name'))))

                    if holerite.employee_id.ramais:
                        validacoes += \
                            _('Ramais ainda na responsabilidade do '
                              'funcionário:\n {} '.format(' - '.join(
                            holerite.employee_id.ramais.mapped('name'))))

                    if validacoes:
                        raise exceptions.Warning(validacoes)

                # setar as ligacoes telefonicas como debitadas
                for ligacao_id in holerite.ligacoes_ids:
                    ligacao_id.state = 'paid'

    @api.multi
    def draft(self):
        for holerite in self:
            if holerite.state == 'verify':
                holerite.write({'state': 'draft'})
                # Atualizar o controle de férias, o controle de férias do
                # contrato é baseado nos holerites validados
                if holerite.tipo_de_folha in ['rescisao_complementar']:
                    pass
                elif holerite.tipo_de_folha in ['rescisao']:
                    holerite.sudo().contract_id.action_button_update_controle_ferias()
                else:
                    holerite.contract_id.action_button_update_controle_ferias()

                # setar as ligacoes telefonicas como atestadas
                for ligacao_id in holerite.ligacoes_ids:
                    ligacao_id.write({'state': 'validate'})

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.data_mes_ano and record.contract_id:
                name = record.contract_id.nome_contrato + ' ' + \
                    record.data_mes_ano
            result.append((record.id, name))
        return result

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

    @api.model
    def compute_payment_day(self, date):
        res = fields.Datetime.from_string(date) + relativedelta(days=-1)
        rc = self.env['resource.calendar']
        end = 1
        while end < 2:
            if rc.data_eh_dia_util(res):
                end += 1
                res = res + relativedelta(days=-1)
            else:
                res = res + relativedelta(days=-2)
        return res.date()

    @profile
    @api.multi
    @api.depends('line_ids')
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
                # elif line.code in ['BASE_INSS', 'BASE_INSS_13']:
                #     base_inss += line.total
                elif line.code == 'BASE_IRPF':
                    base_irpf = line.total
                elif line.code == 'FGTS':
                    fgts = line.total
                elif line.code == 'INSS':
                    inss = line.total
                elif line.code == 'IRPF':
                    irpf = line.total

            soma_base_inss = 0

            base_inss = \
                holerite.line_ids.filtered(lambda x: x.code == 'BASE_INSS')

            if base_inss:
                soma_base_inss = base_inss[0].total

            base_inss_13 = \
                holerite.line_ids.filtered(lambda x: x.code == 'BASE_INSS_13')

            if base_inss_13:
                soma_base_inss += base_inss_13.total

            holerite.total_folha = total
            holerite.total_proventos = total_proventos
            holerite.total_descontos = total_descontos
            holerite.base_fgts = base_fgts
            holerite.base_inss = soma_base_inss
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
            holerite.base_fgts_fmt = valor.formata_valor(holerite.base_fgts) \
                if holerite.base_fgts > 0 else 0.00
            holerite.base_inss_fmt = valor.formata_valor(holerite.base_inss)
            holerite.base_irpf_fmt = valor.formata_valor(holerite.base_irpf)
            holerite.fgts_fmt = valor.formata_valor(holerite.fgts) \
                if holerite.fgts > 0 else 0.00
            holerite.inss_fmt = valor.formata_valor(holerite.inss)
            holerite.irpf_fmt = valor.formata_valor(holerite.irpf)
            holerite.data_extenso = data.data_por_extenso(fields.Date.today())
            holerite.data_retorno = data.formata_data(
                str((fields.Datetime.from_string(holerite.date_to) +
                     relativedelta(days=1)).date()))
            holerite.data_pagamento = str(
                self.compute_payment_day(holerite.date_from))
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

    employee_id = fields.Many2one(
        string=u'Funcionário',
        comodel_name='hr.employee',
        compute='_compute_set_employee_id',
        store=True,
        required=False,
        states={'draft': [('readonly', False)]}
    )

    contract_id = fields.Many2one(
        domain="[('tipo','=','funcionario')]",
    )

    is_simulacao = fields.Boolean(
        string=u"Simulação",
    )

    eh_mes_comercial = fields.Boolean(
        string=u"Mês Comercial?",
    )

    salary_unit_code = fields.Char(
        string='Tipo de Remuneração',
    )

    valor_tarefa = fields.Float(
        string=u'Valor da Tarefa',
        help=u'Valor da tarefa exporádica (autônomos) quando o Unidade de '
             u'Salário definida no contrato for: "Remuneração por tarefa."',
    )

    @api.depends('contract_id', 'dias_aviso_previo_trabalhados')
    @api.multi
    def _calcular_dias_aviso_previo(self):
        for payslip in self:
            if payslip.contract_id:
                periodos_aquisitivos = self.env['hr.vacation.control'].search(
                    [
                        ('contract_id', '=', payslip.contract_id.id)
                    ]
                )[1:]
                tempo_trabalhado = []
                tempo_trabalhado = [
                    ano.inicio_aquisitivo for ano in periodos_aquisitivos if
                    ano.inicio_aquisitivo not in tempo_trabalhado]

                payslip.dias_aviso_previo = \
                    30 + (len(tempo_trabalhado) * 3) - \
                    payslip.dias_aviso_previo_trabalhados
            else:
                payslip.dias_aviso_previo = 0

    dias_aviso_previo = fields.Integer(
        string="Dias de Aviso Prévio",
        compute=_calcular_dias_aviso_previo
    )
    dias_aviso_previo_trabalhados = fields.Integer(
        string="Dias de Aviso Prévio Trabalhados",
        default=0,
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

    struct_id = fields.Many2one(
        string=u'Estrutura de Salário',
        comodel_name='hr.payroll.structure',
        compute='_compute_set_employee_id',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help=u'Defines the rules that have to be applied to this payslip, '
             u'accordingly to the contract chosen. If you let empty the field '
             u'contract, this field isn\'t mandatory anymore and thus the '
             u'rules applied will be all the rules set on the structure of all'
             u' contracts of the employee valid for the chosen period'
    )

    mes_do_ano = fields.Selection(
        selection=MES_DO_ANO,
        string=u'Mês',
        required=True,
        default=datetime.now().month,
    )

    mes_do_ano2 = fields.Selection(
        selection=MES_DO_ANO2,
        string=u'Mês',
        required=True,
        default=datetime.now().month,
    )

    @api.onchange('mes_do_ano2')
    def on_change_mes_do_ano(self):
        self.mes_do_ano = self.mes_do_ano2

    ano = fields.Integer(
        string=u'Ano',
        default=datetime.now().year,
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

    data_admissao_fmt = fields.Char(
        string=u'Data de admissao',
        default='0',
        compute='_compute_valor_total_folha'
    )

    salario_base_fmt = fields.Char(
        string=u'Salario Base',
        default='0',
        compute='_compute_valor_total_folha'
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

    base_fgts = fields.Float(
        string=u'Base do FGTS',
        default=0.00,
        compute='_compute_valor_total_folha'
    )

    base_fgts_fmt = fields.Char(
        string=u'Base do FGTS',
        default='0',
        compute='_compute_valor_total_folha'
    )

    base_inss = fields.Float(
        string=u'Base do INSS',
        default=0.00,
        compute='_compute_valor_total_folha'
    )

    base_inss_fmt = fields.Char(
        string=u'Base do INSS',
        default='0',
        compute='_compute_valor_total_folha'
    )

    base_irpf = fields.Float(
        string=u'Base do IRPF',
        default=0.00,
        compute='_compute_valor_total_folha'
    )

    base_irpf_fmt = fields.Char(
        string=u'Base do IRPF',
        default='0',
        compute='_compute_valor_total_folha'
    )

    fgts = fields.Float(
        string=u'FGTS',
        default=0.00,
        compute='_compute_valor_total_folha'
    )

    fgts_fmt = fields.Char(
        string=u'FGTS',
        default='0',
        compute='_compute_valor_total_folha'
    )

    inss = fields.Float(
        string=u'INSS',
        default=0.00,
        compute='_compute_valor_total_folha'
    )

    inss_fmt = fields.Char(
        string=u'INSS',
        default='0',
        compute='_compute_valor_total_folha'
    )

    irpf = fields.Float(
        string=u'IRPF',
        default=0.00,
        compute='_compute_valor_total_folha'
    )

    irpf_fmt = fields.Char(
        string=u'IRPF',
        default='0',
        compute='_compute_valor_total_folha'
    )

    data_extenso = fields.Char(
        string=u'Data por Extenso',
        compute='_compute_valor_total_folha'
    )

    data_retorno = fields.Char(
        string=u'Data de Retorno',
        compute='_compute_valor_total_folha'
    )

    data_pagamento = fields.Char(
        string=u'Data de Pagamento de férias',
        compute='_compute_valor_total_folha',
    )

    inicio_aquisitivo = fields.Date(
        string=u'Início do Período Aquisitivo',
        compute='_compute_periodo_aquisitivo',
        store=True,
    )
    fim_aquisitivo = fields.Date(
        string=u'Fim do Período Aquisitivo',
        compute='_compute_periodo_aquisitivo',
        store=True,
    )

    @api.multi
    @api.depends('periodo_aquisitivo')
    def _compute_periodo_aquisitivo(self):
        for holerite in self:
            if holerite.periodo_aquisitivo:
                holerite.inicio_aquisitivo = \
                    holerite.periodo_aquisitivo.inicio_aquisitivo
                holerite.fim_aquisitivo = \
                    holerite.periodo_aquisitivo.fim_aquisitivo

    inicio_aquisitivo_fmt = fields.Char(
        string=u'Inicio do Período Aquisitivo Formatado',
        compute='_compute_valor_total_folha',
    )
    fim_aquisitivo_fmt = fields.Char(
        string=u'Fim do Período Aquisitivo Formatado',
        compute='_compute_valor_total_folha',
    )
    inicio_gozo_fmt = fields.Char(
        string=u'Inicio do Período de Gozo Formatado',
        compute='_compute_valor_total_folha',
    )
    fim_gozo_fmt = fields.Char(
        string=u'Fim do Periodo de Gozo Formatado',
        compute='_compute_valor_total_folha',
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

    date_from = fields.Date(
        string='Date From',
        # readonly=True,
        # states={'draft': [('readonly', False)]},
        required=True,
        # compute='_compute_set_dates',
        # store=True,
    )

    date_to = fields.Date(
        string='Date To',
        # readonly=True,
        # states={'draft': [('readonly', False)]},
        required=True,
        # compute='_compute_set_dates',
        # store=True,
    )

    saldo_para_fins_rescisorios = fields.Float(
        string='Saldo para fins Rescisorios',
    )

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
        # compute='_compute_set_dates',
        # store=True,
    )

    data_inicio_periodo_aquisitivo = fields.Date(
        string="Inicio do Período Aquisitivo",
        related="periodo_aquisitivo.inicio_aquisitivo",
        store=True,
    )

    data_fim_periodo_aquisitivo = fields.Date(
        string="Fim do Período Aquisitivo",
        related="periodo_aquisitivo.fim_aquisitivo",
        store=True,
    )

    # Rescisão
    data_afastamento = fields.Date(
        string="Data do afastamento"
    )

    data_pagamento_demissao = fields.Date(
        string="Data do pagamento"
    )

    data_pagamento_competencia = fields.Date(
        string="Data do pagamento",
    )

    valor_saldo_fgts = fields.Float(
        string="Valor do Saldo do FGTS"
    )

    valor_multa_fgts = fields.Float(
        string="Valor da Multa do FGTS"
    )

    ferias_vencidas = fields.Many2one(
        comodel_name='hr.vacation.control',
        string="Ferias Vencidas",
        domain="[('contract_id','=',contract_id)]",
        compute='_verificar_ferias_vencidas',
        store=True,
    )

    company_id = fields.Many2one(
        string="Empresa",
        comodel_name="res.company",
        related=False,
        store=True,
    )

    rescisao_ids = fields.One2many(
        comodel_name='hr.campos.rescisao',
        inverse_name='slip_id',
        string=u'Campo de Rescisão'
    )

    ligacoes_ids = fields.One2many(
        comodel_name='hr.telefonia.line',
        inverse_name='payslip_id',
        string=u'Ligações',
    )
    mtv_deslig = fields.Char(
        string='Motivo Desligamento',
    )
    valor_pgto_aviso_previo_indenizado = fields.Float(
        string='Aviso Prévio Indenizado',
        compute='_compute_aviso_previo_indenizado',
        inverse='_set_aviso_previo_indenizado',
    )

    @api.multi
    def _compute_aviso_previo_indenizado(self):
        """
        Buscar valor do pagamento de aviso prévio indenizado
        :return:
        """
        for record in self:
            for rubrica in record.line_ids:
                if rubrica.code == "AVISO_PREV_IND":
                    return rubrica.total
            return 0.0

    @profile
    @api.multi
    def _set_aviso_previo_indenizado(self):
        """
        Função para setar o valor do aviso previo indenizado
        :return:
        """
        for record in self:
            pass

    @profile
    @api.multi
    def buscar_pensao_alimenticia(self):
        """
        Verificar se o empregado do contrato paga pensão alimentícia
        :return:
        """
        for dependente in self.contract_id.employee_id.dependent_ids:
            if dependente.have_alimony:
                return True

        return False

    @api.depends('periodo_aquisitivo')
    @api.model
    def _compute_saldo_periodo_aquisitivo(self):
        for holerite in self:
            if holerite.periodo_aquisitivo:
                holerite.saldo_periodo_aquisitivo = \
                    holerite.periodo_aquisitivo.saldo
            # Campo para configurar o saldo do Período aquisitivo manualmente.
            # Para gerar provisão simulando o passado
            if holerite.saldo_periodo_aquisitivo_manual:
                holerite.saldo_periodo_aquisitivo = \
                    holerite.saldo_periodo_aquisitivo_manual

    saldo_periodo_aquisitivo = fields.Float(
        string="Saldo de dias do Periodo Aquisitivo",
        compute='_compute_saldo_periodo_aquisitivo',
        help=u'Saldo de dias do funcionaŕio, de acordo com número de faltas'
             u'dentro do período aquisitivo selecionado.',
    )

    saldo_periodo_aquisitivo_manual = fields.Float(
        string="Forçar Saldo do Periodo Aquisitivo",
    )

    @profile
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
            if payslip.state not in ['draft', 'cancel']:
                raise exceptions.Warning(
                    _('You cannot delete a payslip which is not '
                      'draft or cancelled or permission!')
                )
            payslip.cancel_sheet()
        return super(HrPayslip, self).unlink()

    @api.multi
    def get_worked_day_lines(self, contract_id, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should
        be applied for the given contract between date_from and date_to
        """
        result = []
        resource_calendar_obj = self.env['resource.calendar']
        for contract_id in self.env['hr.contract'].browse(contract_id):

            #
            # GET dias Base para cálculo do mês
            #

            # DIAS no mês
            # Verificação do 13 salario
            mes_do_ano = \
                str(self.mes_do_ano) if str(self.mes_do_ano) != '13' else '12'
            primeiro_dia_do_mes = \
                str(datetime.strptime(
                    mes_do_ano + '-' + str(self.ano), '%m-%Y'))[:10]
            ultimo_dia_do_mes = str(ultimo_dia_mes(primeiro_dia_do_mes))
            dias_mes = resource_calendar_obj.get_dias_base(
                fields.Datetime.from_string(primeiro_dia_do_mes),
                fields.Datetime.from_string(ultimo_dia_do_mes),
                mes_comercial=self.eh_mes_comercial,
            )

            # Na rescisao, os calculos de férias deverao ser sob 30 dias
            # Ferias indenizaddas deverão ser mes comercial
            if self.tipo_de_folha == 'ferias' and self.is_simulacao:
                dias_mes = 30

            result += [self.get_attendances(
                u'Dias no Mês Atual', 20, u'DIAS_MES_COMPETENCIA_ATUAL',
                dias_mes, 0.0, contract_id)]

            # Utilizar mes civil
            dias_mes = resource_calendar_obj.get_dias_base(
                fields.Datetime.from_string(date_from),
                fields.Datetime.from_string(date_to),
                mes_comercial=self.eh_mes_comercial,
            )

            if self.tipo_de_folha == 'rescisao':
                # Quando o afastamento for no primeiro dia do mes,
                # significa que nao trabalhou nenhum dia
                if self.data_afastamento == primeiro_dia_do_mes[:10]:
                    dias_mes = 0

                # Ajuste temporário!
                # Se na rescisao ja tiver sido calculado o holerite do mes:
                # Holerite março gerado em 17/mar referente a 1/mar ate 30/mar
                # rescisao feita no dia 30/mar
                # Zerar os dias do mes pois ja foram pagos no holerite
                # Quando rescisao o metodo set_dates da payslip, encarega de
                #  igualar o dat_from e date_to do holerite à data de afastam.
                if self.data_afastamento == self.date_to and \
                        self.data_afastamento == self.date_to:
                    dias_mes = 0

            result += [self.get_attendances(
                u'Dias Base', 30, u'DIAS_BASE', dias_mes, 0.0, contract_id)]

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

            leaves = self.env['hr.holidays'].get_ocurrences(
                hr_contract.employee_id.id, date_from, date_to)

            if leaves.get('faltas_nao_remuneradas'):
                qtd_leaves = leaves['quantidade_dias_faltas_nao_remuneradas']
                result += [self.get_attendances(u'Faltas Não remuneradas', 31,
                                                u'FALTAS_NAO_REMUNERADAS',
                                                qtd_leaves,
                                                0.0, contract_id)]

            if leaves.get('faltas_remuneradas'):
                qtd_leaves = leaves['quantidade_dias_faltas_remuneradas']
                result += [self.get_attendances(
                    u'Faltas remuneradas', 32, u'FALTAS_REMUNERADAS',
                    qtd_leaves, 0.0, contract_id)]

            # get Quantidade de DSR
            quantity_DSR = hr_contract.working_hours. \
                quantidade_de_DSR(date_from, date_to)
            if quantity_DSR:
                result += [self.get_attendances(u'DSR do Mês', 4,
                                                u'DSR_TOTAL', quantity_DSR,
                                                0.0, contract_id)]
            # get discount DSR
            quantity_DSR_discount = \
                self.env['resource.calendar'].get_quantity_discount_DSR(
                    leaves['faltas_nao_remuneradas'] + leaves[
                        'faltas_remuneradas'],
                    hr_contract.working_hours.leave_ids, date_from, date_to)

            result += [self.get_attendances(
                u'DSR a serem descontados', 33, u'DSR_PARA_DESCONTAR',
                quantity_DSR_discount, 0.0, contract_id)]

            #
            # GET dias de FERIAS + get dias de ABONO pecuniario
            #
            if self.tipo_de_folha == 'provisao_ferias' or self.is_simulacao:
                quantidade_dias_abono = 0
                quantidade_dias_ferias = self.saldo_periodo_aquisitivo
            else:
                quantidade_dias_ferias, quantidade_dias_abono = \
                    self.env['resource.calendar'].get_quantidade_dias_ferias(
                        hr_contract, date_from, date_to)

            result += [
                self.get_attendances(
                    u'Quantidade dias em Férias', 34, u'FERIAS',
                    quantidade_dias_ferias, 0.0, contract_id
                )
            ]

            result += [
                self.get_attendances(
                    u'Quantidade dias Abono Pecuniario', 35,
                    u'ABONO_PECUNIARIO', quantidade_dias_abono,
                    0.0, contract_id
                )
            ]
            # se o periodo aquisitivo ja estiver definido, pega o saldo de dias
            if self.periodo_aquisitivo:
                saldo_ferias = 0
                if self.periodo_aquisitivo:
                    saldo_ferias = self.periodo_aquisitivo.saldo
                # if self.tipo_de_folha in ['rescisao'] or fields.\
                #        Date.from_string(self.date_from) < fields.Date.\
                #        from_string(self.periodo_aquisitivo.inicio_concessivo):
                #    saldo_ferias = \
                #        self.periodo_aquisitivo.dias_de_direito() *\
                #        self.medias_proventos[0]['meses'] / 12.0
                # else:
                # if self.tipo_de_folha == 'ferias' and self.is_simulacao and \
                #        self.date_to and self.date_from:
                #    dias_saldo = fields.Datetime.from_string(self.date_to) - \
                #        fields.Datetime.from_string(self.date_from)
                #    saldo_ferias = dias_saldo.days
                # else:
                #    saldo_ferias = self.periodo_aquisitivo.avos * 2.5

                result += [
                    self.get_attendances(
                        u'Saldo de dias máximo para Férias', 8,
                        u'SALDO_FERIAS', saldo_ferias,
                        0.0, contract_id
                    )
                ]

            #
            # GET dias de FERIAS na competencia ATUAL (caso de ferias quebrada)
            #
            quantidade_dias_ferias, quantidade_dias_abono = \
                self.env['resource.calendar'].get_quantidade_dias_ferias(
                    hr_contract, primeiro_dia_do_mes, ultimo_dia_do_mes)

            # PAra Simulações da rescisao e provisão da folha
            if self.tipo_de_folha == 'provisao_ferias' or self.is_simulacao:
                quantidade_dias_abono = 0
                quantidade_dias_ferias = self.saldo_periodo_aquisitivo

            result += [self.get_attendances(
                u'Quantidade dias em Férias na Competência Atual', 38,
                u'FERIAS_COMPETENCIA_ATUAL', quantidade_dias_ferias, 0.0,
                contract_id
            )]

            #
            # GET dias FERIAS na competencia SEGUINTE(caso de ferias quebrada)
            #
            mes_do_ano_ferias = self.mes_do_ano + 1 if self.mes_do_ano < 12 else 1
            ano_ferias = self.ano if self.mes_do_ano < 12 else self.ano + 1
            primeiro_dia_do_mes_seguinte = \
                str(datetime.strptime(str(
                    mes_do_ano_ferias) + '-' + str(ano_ferias), '%m-%Y').date())
            ultimo_dia_do_mes_seguinte = \
                str(ultimo_dia_mes(primeiro_dia_do_mes_seguinte))
            quantidade_dias_ferias_competencia_seguinte, \
            quantidade_dias_abono_competencia_seguinte = \
                self.env['resource.calendar'].get_quantidade_dias_ferias(
                    hr_contract, primeiro_dia_do_mes_seguinte,
                    ultimo_dia_do_mes_seguinte)

            # PAra Simulações da rescisao e provisão da folha
            if self.tipo_de_folha == 'provisao_ferias' or self.is_simulacao:
                quantidade_dias_ferias_competencia_seguinte = 0

            result += [self.get_attendances(
                u'Quantidade dias em Férias na Competência Seguinte', 39,
                u'FERIAS_COMPETENCIA_SEGUINTE',
                quantidade_dias_ferias_competencia_seguinte, 0.0, contract_id
            )]

            #
            # GET dias totais do Mês seguinte
            #
            dias_mes_seguinte = resource_calendar_obj.get_dias_base(
                fields.Datetime.from_string(primeiro_dia_do_mes_seguinte),
                fields.Datetime.from_string(ultimo_dia_do_mes_seguinte),
                mes_comercial=self.eh_mes_comercial,
            )
            result += [self.get_attendances(
                u'Dias no Mês seguinte', 22, u'DIAS_MES_COMPETENCIA_SEGUINTE',
                dias_mes_seguinte, 0.0, contract_id)]

            #
            # GET Dias Trabalhados
            #
            quantidade_dias_trabalhados = \
                dias_mes - leaves['quantidade_dias_faltas_nao_remuneradas'] - \
                quantity_DSR_discount - quantidade_dias_ferias
            result += [self.get_attendances(u'Dias Trabalhados', 36,
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
        salario_mes_proporcional_dic = {
            'name': 'Salário Mês Proporcional',
            'code': 'SALARIO_MES_PROPORCIONAL',
            'amount': contract._salario_mes_proporcional(date_from, date_to),
            'contract_id': contract.id,
        }
        salario_mes_inicial_dic = {
            'name': 'Salário Mês Inicial',
            'code': 'SALARIO_MES_INICIAL',
            'amount': contract._salario_mes_inicial(date_from, date_to),
            'contract_id': contract.id,
        }

        # Caso tenha alteracao contratual no mês corrente, o provisionamento
        # devera calcular com a remuneração alterada. Por isso na busca
        # do salario, levamos em conta o inicio e o fim do mes. O sistema entao
        # encontrara as alterações caso existam naquele mes
        if self.tipo_de_folha in ['provisao_ferias',
                                  'provisao_decimo_terceiro']:
            date_from = str(self.ano).zfill(4) + '-' + \
                        str(self.mes_do_ano).zfill(2) + '-01'
            date_to = str(ultimo_dia_mes(date_from))

        salario_mes_final_dic = {
            'name': 'Salário Mês Final',
            'code': 'SALARIO_MES_FINAL',
            'amount': contract._salario_mes_final(date_from, date_to),
            'contract_id': contract.id,
        }
        res += [salario_mes_inicial_dic]
        res += [salario_mes_final_dic]
        res += [salario_mes_proporcional_dic]
        res += [salario_mes_dic]
        res += [salario_dia_dic]
        res += [salario_hora_dic]
        return res

    @profile
    def INSS(self, BASE_INSS):
        """
        Cálculo do INSS da folha de pagamento. Essa função é responsável por
        disparar o cálculo do INSS, que fica embutido em sua classe.
         Essa função está dísponivel no context das rubricas sendo possível
         inserir o seguinte código python na rubrica:
         result = CALCULAR.INSS(<variavel que contem a base do INSS>)
         *CALCULAR é a instancia corrente da payslip
        :param BASE_INSS: - float - soma das rubricas que compoe o INSS
        :return: float - Valor do inss a ser descontado do funcionario
        """
        tabela_inss_obj = self.env['l10n_br.hr.social.security.tax']
        if BASE_INSS:
            inss, reference = tabela_inss_obj._compute_inss(BASE_INSS,
                                                            self.date_from)
            return inss, reference
        else:
            return 0, ' '

    @profile
    def BASE_IRRF(self, TOTAL_IRRF, INSS):
        """
        Calcula a base de cálculo do IRRF. A formula se da por:
        BASE_IRRF = BASE_INSS - INSS -
            (DESCONTO_POR_DEPENDENTE * QTY_DE_DEPENDENTES)

        :param TOTAL_IRRF:  - float - Soma das rubricas que compoem a BASE_IRRF
        :param INSS:        - float - Valor do INSS a ser descontado
                                      do funcionario
        :return:            - float - base do IRRF
        """
        ano = fields.Datetime.from_string(self.date_from).year

        dependent_values = self.get_dependent_values_irrf(ano)

        return TOTAL_IRRF - INSS - dependent_values

    @profile
    def get_dependent_values_irrf(self, ano):
        deducao_dependente_obj = self.env[
            'l10n_br.hr.income.tax.deductable.amount.family'
        ]
        deducao_dependente_value = deducao_dependente_obj.search(
            [('year', '=', ano)], order='create_date DESC', limit=1
        )
        dependent_values = 0
        for dependente in self.employee_id.dependent_ids:
            if dependente.dependent_verification and \
                    dependente.dependent_dob <= self.date_to:
                dependent_values += deducao_dependente_value.amount
        return dependent_values

    @profile
    def IRRF(self, BASE_IRRF, INSS):
        tabela_irrf_obj = self.env['l10n_br.hr.income.tax']
        if BASE_IRRF:
            irrf, reference = tabela_irrf_obj._compute_irrf(
                BASE_IRRF, self.employee_id.id, INSS, self.date_from
            )
            return irrf, reference
        else:
            return 0, ' '

    @profile
    def INSS_vinculo_cedente(self):
        """
        Verificar se no vínculo anterior já houve alguma contribuição com a
        seguridade social
        """
        inss_vinculo_obj = self.env['hr.contribuicao.inss.vinculos']

        period_id = self.env['account.period'].find(self.date_from)

        inss_vinculos_id = inss_vinculo_obj.search([
            ('contrato_id', '=', self.contract_id.id),
            ('period_id', '=', period_id.id),
        ], limit=1)

        if inss_vinculos_id:
            return inss_vinculos_id.valor_alicota_vinculo

        return 0

    @profile
    def MEDIA_RUBRICA(self, codigo, tipo_de_folha='normal'):

        final_periodo = '{}-{:02}-{:02}'.format(self.ano, self.mes_do_ano2, 1)
        final_periodo = str(ultimo_dia_mes(final_periodo))

        if self.tipo_de_folha in ['ferias', 'provisao_ferias']:

            inicio_periodo = self.periodo_aquisitivo.inicio_aquisitivo

            inicio_periodo = '{}-{}-01'.format(
                inicio_periodo[:4], inicio_periodo[5:7])

            # Na provisao pegar a data do mes que esta sendo provisionado,
            # para o periodo aquisitivo do ano. Isso filtra as buscas de
            # holerites de média até a competencia que esta sendo provisionada
            if self.periodo_aquisitivo.fim_aquisitivo < final_periodo:
                final_periodo = self.periodo_aquisitivo.fim_aquisitivo

        elif self.tipo_de_folha in ['decimo_terceiro',
                                    'provisao_decimo_terceiro']:
            #
            # Calcular o período desejado e a quantidade de meses
            # Para ser usado no cálculo da média
            #
            inicio_periodo = '{}-12-01'.format(self.ano - 1)

            if self.contract_id.date_start > inicio_periodo:
                inicio_periodo = self.contract_id.date_start

        """
        Considerando que as gratificações, prêmios e adicionais fixos,
         habitualmente pagos ao empregado, integram o salário para
          apuração do 13º salário por sua média duodecimal, 
          independentemente da periodicidade de seu pagamento, 
          bem como todas as verbas estabelecidas no artigo 457 da CLT. 
          As horas extras e horas noturnas, se habituais, possuem 
          natureza salarial, integrando ao salário do empregado para 
          todos os efeitos legais,conforme as Súmulas TST nºs 60 e 347.
          10 de maio de 2019.
        """
        # Conforme e-mail enviado pela GECON-ABGF no dia 14/03/2018 às
        # 16h52, foi considerado para o cálculo das médias o mês "cheio"
        # e para o cálculo dos avos, foi aplicada a regra dos 15 dias de
        # trab.
        meses = 12

        domain = [
            ('contract_id', '=', self.contract_id.id),
            ('tipo_de_folha', '=', 'normal'),
            ('state', 'in', ['done', 'verify']),
            ('date_from', '>=', inicio_periodo),
            ('date_to', '<=', final_periodo),
        ]

        #
        # Buscar dentro dos holerites pela rubrica requerida
        #
        folha_obj = self.env['hr.payslip']
        folhas_periodo = folha_obj.search(domain)
        folhas_periodo = folhas_periodo.sorted(key=lambda r: r.date_from)

        valor = 0
        for holerite in folhas_periodo:
            for linha in holerite.line_ids:
                if linha.salary_rule_id.code == codigo:
                    valor += linha.total
                    _logger.info('{} - {}'.format(
                        holerite.data_mes_ano, linha.total))

        # # Validar Media
        l10n_br_hr_media = self.medias_proventos.filtered(
            lambda x: x.rubrica_id.code == codigo)

        if l10n_br_hr_media:
            if not l10n_br_hr_media.soma == valor:
                _logger.info('\n\nERRO: Valores de média e aba de "Cálculo'
                             'de Médias do Holerite estão divergentes!\n')

        media = valor / meses

        return media

    @profile
    @api.multi
    def get_contract_specific_rubrics(
            self, applied_specific_rule, rule_ids, DIAS_A_MAIOR):
        """
        Caso nao esteja computando holerite de provisão de ferias ou
        de decimo terceiro recuperar as regras especificas do contrato

        Quando for rescisao, verificar se ja foi calculado o holerite
        do mes. Só aplicar as rubricas especificas se nao possuir
        DIAS_A_MAIOR

        :param rule_ids:
        :param DIAS_A_MAIOR: (Dias pagos no holerite normal procesado antes
        da rescisao)
        :return:
        """
        self.ensure_one()

        for specific_rule in self.contract_id.specific_rule_ids:

            tipo_holerite = True if specific_rule.tipo_holerite in [
                self.tipo_de_folha, 'all'] else False

            if tipo_holerite:

                if self.date_from >= specific_rule.date_start:
                    if not specific_rule.date_stop or \
                            self.date_to <= specific_rule.date_stop:
                        rule_ids.append((specific_rule.rule_id.id,
                                         specific_rule.rule_id.sequence))

                        specific = {
                            'type': 'contract',
                            'rule_id': specific_rule,
                            'beneficiario_id': specific_rule.partner_id,
                            'ref': specific_rule.ref,
                            'value': (
                                specific_rule.specific_quantity *
                                specific_rule.specific_percentual / 100 *
                                specific_rule.specific_amount,

                                specific_rule.specific_quantity,

                                specific_rule.specific_percentual,
                                specific_rule.ref
                            )
                        }
                        applied_specific_rule[specific_rule.rule_id.id].append(
                            specific
                        )

    @profile
    def get_ferias_rubricas(self, payslip, rule_ids):
        holerite_ferias = self.search([
            ('tipo_de_folha', '=', 'ferias'),
            ('date_from', '>=', payslip.date_from),
            ('date_from', '<=', payslip.date_to),
            ('contract_id', '=', payslip.contract_id.id),
            ('state', 'in', ['done', 'verify'])
        ])
        if holerite_ferias:
            for line in holerite_ferias.line_ids:
                if line.code == 'BASE_FERIAS':
                    continue
                rule_ids.append(
                    (line.salary_rule_id.id, line.salary_rule_id.sequence))
        return rule_ids, holerite_ferias.holidays_ferias

    @profile
    def buscar_ferias_do_mes(self, payslip):
        """
        Buscar holerite de ferias que tem o inicio dentro do mes da competencia
        que esta sendo calculada. Isto é, quando estiver sendo calculado o
        holerite de OUTUBRO, buscar férias que tem a data inicial em OUT.
        """
        holerite_ferias = self.search([
            ('tipo_de_folha', '=', 'ferias'),
            ('date_from', '>=', payslip.date_from),
            ('date_from', '<=', payslip.date_to),
            ('contract_id', '=', payslip.contract_id.id),
            ('state', 'in', ['done', 'verify']),
            ('is_simulacao', '=', False)
        ])
        if holerite_ferias:
            lines = []
            for line in holerite_ferias.line_resume_ids:
                lines.append(line)
        else:
            return False, False
        return lines, holerite_ferias.holidays_ferias

    @profile
    def get_specific_rubric_value(self, rubrica_id, references=False):
        """
        Função dísponivel para as regras de salario, que busca o valor das
        rubricas especificas cadastradas no contrato.
        :param rubrica_id: int - id da regra de salario corrente
        :param rubricas_spec_calculadas - lista dos ids das rubricas
                                        especificas que ja foram computadas
        :return: valor da rubrica especifica cadastrado no contrato ou 0.
        """
        for rubrica in self.contract_id.specific_rule_ids:

            if references and references.get(rubrica.rule_id.id):
                if rubrica.ref and rubrica.ref in references.get(
                        rubrica.rule_id.id):
                    continue

            if rubrica.rule_id.id == rubrica_id \
                    and rubrica.date_start <= self.date_from and \
                    (not rubrica.date_stop or rubrica.date_stop >=
                     self.date_to):
                return (
                    rubrica.specific_quantity *
                    rubrica.specific_percentual / 100 *
                    rubrica.specific_amount,

                    rubrica.specific_quantity,

                    rubrica.specific_percentual,
                    rubrica.ref
                )
        return 0

    @profile
    @api.multi
    def get_desconto_ligacao_telefonica(self):
        """
        Função para buscar descontos de ligacoes telefonicas atestadas pelo 
        funcionario
        :return:
        """
        ligacao_obj = self.env['hr.telefonia.line']
        for holerite_id in self:

            # Desvincular antigas
            holerite_id.ligacoes_ids = False

            domain = [
                ('state', '=', 'validate'),
                ('tipo', '=', 'particular'),
                ('employee_id', '=', holerite_id.contract_id.employee_id.id),
                ('payslip_id', '=', False)
            ]
            ligacoes_ids = ligacao_obj.search(domain)
            if ligacoes_ids:
                # Criar relacao  entre a ligacao e o holerite
                for ligacao_id in ligacoes_ids:
                    ligacao_id.payslip_id = holerite_id.id
                return sum(ligacoes_ids.mapped('valor'))
            return 0.0

    @profile
    @api.multi
    def _buscar_valor_salario(self, codigo):
        for tipo_salario in self.input_line_ids:
            if tipo_salario.code == codigo:
                return tipo_salario.amount
        return 0.00

    @profile
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

    @profile
    @api.multi
    def buscar_estruturas_salario(self):
        if self.tipo_de_folha in \
                ['normal', 'aviso_previo', 'rescisao_complementar']:
            return self.contract_id.struct_id
        elif self.tipo_de_folha == "decimo_terceiro":
            if self.is_simulacao:
                estrutura_decimo_terceiro = \
                    self.contract_id.struct_id.estrutura_13_id
                return estrutura_decimo_terceiro
            else:
                if self.mes_do_ano <= 12:
                    estrutura_decimo_terceiro = \
                        self.contract_id.struct_id.estrutura_adiantamento_13_id
                    return estrutura_decimo_terceiro
                else:
                    estrutura_decimo_terceiro = \
                        self.contract_id.struct_id.estrutura_13_id
                    return estrutura_decimo_terceiro
        elif self.tipo_de_folha == "ferias":
            estrutura_ferias = \
                self.contract_id.struct_id.estrutura_ferias_id
            return estrutura_ferias
        elif self.tipo_de_folha == "rescisao":
            estrutura_rescisao = self.env['hr.payroll.structure'].search(
                [('code', '=', 'RESCISAO')], limit=1
            )
            return estrutura_rescisao
        elif self.tipo_de_folha == "provisao_ferias":
            estrutura_provisao_ferias = \
                self.contract_id.struct_id.estrutura_ferias_id
            return estrutura_provisao_ferias
        elif self.tipo_de_folha == "provisao_decimo_terceiro":
            estrutura_provisao_decimo_terceiro = \
                self.contract_id.struct_id.estrutura_13_id
            return estrutura_provisao_decimo_terceiro

    @api.depends('contract_id', 'date_from', 'date_to')
    @api.one
    def _verificar_ferias_vencidas(self):
        for record in self:
            periodo_ferias_vencida = self.env['hr.vacation.control'].search([
                ('contract_id', '=', record.contract_id.id),
                ('fim_aquisitivo', '<', record.date_from),
                ('fim_concessivo', '>=', record.date_to),
                ('inicio_gozo', '=', False),
            ], order='fim_aquisitivo desc')
            return periodo_ferias_vencida

    @profile
    @api.multi
    def gerar_simulacao(
            self, tipo_simulacao, mes_do_ano, ano, data_inicio, data_fim,
            ferias_vencida=None, periodo_aquisitivo=None
    ):
        vals = {
            'contract_id': self.contract_id.id,
            'tipo_de_folha': tipo_simulacao,
            'is_simulacao': True,
            'mes_do_ano': mes_do_ano,
            'ano': ano,
            'date_from': data_inicio,
            'date_to': data_fim,
            'employee_id': self.contract_id.employee_id.id,
            'data_afastamento': self.data_afastamento,
        }
        if tipo_simulacao == "aviso_previo":
            vals.update({'dias_aviso_previo': self.dias_aviso_previo})

        payslip_simulacao_criada = self.create(vals)
        if tipo_simulacao == "ferias":
            # periodo_ferias_vencida = False
            # if ferias_vencida:
            #    periodo_ferias_vencida = self._verificar_ferias_vencidas()
            payslip_simulacao_criada.write(
                {
                    'periodo_aquisitivo': periodo_aquisitivo.id
                    #         self.contract_id.vacation_control_ids[0].id if
                    #         not periodo_ferias_vencida else
                    #         periodo_ferias_vencida.id
                }
            )
            # payslip_simulacao_criada._compute_saldo_periodo_aquisitivo()

        if tipo_simulacao in ["ferias", "aviso_previo"]:
            payslip_simulacao_criada.gerar_media_dos_proventos()
        payslip_simulacao_criada._compute_set_employee_id()
        # worked_days_line_ids = \
        #     payslip_simulacao_criada.get_worked_day_lines(
        #         self.contract_id.id, data_inicio, data_fim
        #     )
        # input_line_ids = payslip_simulacao_criada.get_inputs(
        #     self.contract_id.id, data_inicio, data_fim
        # )
        # worked_days_obj = self.env['hr.payslip.worked_days']
        # input_obj = self.env['hr.payslip.input']
        # for worked_day in worked_days_line_ids:
        #     worked_day.update({'payslip_id': payslip_simulacao_criada.id})
        #     worked_days_obj.create(worked_day)
        # for input_id in input_line_ids:
        #     input_id.update({'payslip_id': payslip_simulacao_criada.id})
        #     input_obj.create(input_id)
        payslip_simulacao_criada.atualizar_worked_days_inputs()
        payslip_simulacao_criada.compute_sheet()
        payslip_simulacao_criada.write({'paid': True, 'state': 'done'})
        return payslip_simulacao_criada

    @profile
    @api.multi
    def _buscar_valor_bruto_simulacao(
            self, payslip_simulacao, um_terco_ferias=None):
        categoria_bruto = self.env.ref(
            'hr_payroll.BRUTO'
        )
        for line in payslip_simulacao.line_ids:
            if payslip_simulacao.tipo_de_folha == "ferias":
                if line.salary_rule_id.code == "FERIAS" and \
                        not um_terco_ferias:
                    return line.total
                elif line.salary_rule_id.code in \
                        ['1/3_FERIAS', '1/3_FERIAS_S_ONUS'] and um_terco_ferias:
                    return line.total
            else:
                if line.salary_rule_id.category_id.id == categoria_bruto.id:
                    return line.total

    @profile
    @api.multi
    def _checar_datas_gerar_simulacoes(self, mes_do_ano, ano):
        if mes_do_ano > 1:
            mes_do_ano -= 1
        else:
            mes_do_ano = 12
            ano -= 1
        dias_no_mes = monthrange(ano, mes_do_ano)
        data_inicio = str(ano) + "-" + str(mes_do_ano) + "-" + "01"
        data_fim = str(ano) + "-" + str(mes_do_ano) + "-" + str(dias_no_mes[1])
        return mes_do_ano, ano, data_inicio, data_fim

    @profile
    def _simulacao_ferias(self, ferias_vencida, um_terco_ferias):

        #
        # Está buscando somente o último periodo aquisitivo, e se tiver
        # férias vencida busca o penúltimo, essa lógica está incompleta,
        # precisa refatorar esse código para buscar todos os periodos
        # aquisitivos vencidos (TODO)
        #
        if not ferias_vencida:
            periodo_id = self.contract_id.vacation_control_ids[0].id
        else:
            # Se no controle de férias tiver apenas um registro, retorne 0
            if len(self.contract_id.vacation_control_ids) < 2:
                return 0
            periodo_id = self.contract_id.vacation_control_ids[1].id

        self.contract_id.date_end = self.date_to
        self.contract_id.atualizar_data_demissao()

        periodo = self.env['hr.vacation.control'].with_context(
            data_fim=self.data_afastamento).browse(periodo_id)

        if periodo.saldo:
            data_inicio = self.data_afastamento
            data_fim = data.parse_datetime(data_inicio) + relativedelta(
                days=periodo.avos * 2.5)

            domain = [
                ('tipo_de_folha', '=', 'ferias'),
                ('is_simulacao', '=', True),
                ('periodo_aquisitivo', '=', periodo_id)
            ]
            payslip_simulacao = self.env['hr.payslip'].search(domain)
            if payslip_simulacao:
                payslip_simulacao_criada = payslip_simulacao
            else:
                payslip_simulacao_criada = self.gerar_simulacao(
                    'ferias', self.mes_do_ano,
                    self.ano, data_inicio,
                    data_fim, ferias_vencida=ferias_vencida,
                    periodo_aquisitivo=periodo
                )
            return self._buscar_valor_bruto_simulacao(
                payslip_simulacao_criada, um_terco_ferias)

    @profile
    def _simulacao_decimo_terceiro(self):

        data_inicio = self.data_afastamento
        data_fim = self.data_afastamento

        domain = [
            ('tipo_de_folha', '=', 'decimo_terceiro'),
            ('is_simulacao', '=', True),
            ('date_from', '=', data_inicio),
            ('date_to', '=', data_fim),
            ('contract_id', '=', self.contract_id.id),
        ]
        payslip_simulacao = self.env['hr.payslip'].search(domain)
        if payslip_simulacao:
            payslip_simulacao.state = 'draft'
            payslip_simulacao.unlink()

        payslip_simulacao_criada = self.gerar_simulacao(
            'decimo_terceiro', self.mes_do_ano, self.ano, data_inicio, data_fim
        )

        return self._buscar_valor_bruto_simulacao(payslip_simulacao_criada)

    @profile
    @api.multi
    def BUSCAR_VALOR_PROPORCIONAL(
            self, tipo_simulacao, um_terco_ferias=None, ferias_vencida=None):

        # Se simulação férias, faça e saia
        # (ignorando o resto do método, precisa refatorar) (TODO)
        if tipo_simulacao == 'ferias':
            return self._simulacao_ferias(ferias_vencida, um_terco_ferias)

        if tipo_simulacao == 'decimo_terceiro':
            return self._simulacao_decimo_terceiro()

        mes_verificacao, ano_verificacao, data_inicio, data_fim = \
            self._checar_datas_gerar_simulacoes(
                self.mes_do_ano, self.ano
            )
        payslip_simulacao = self.env['hr.payslip']
        if not ferias_vencida:
            if not tipo_simulacao == "ferias":
                payslip_simulacao = self.env['hr.payslip'].search(
                    [
                        ('tipo_de_folha', '=', tipo_simulacao),
                        ('is_simulacao', '=', True),
                        ('mes_do_ano', '=', mes_verificacao),
                        ('ano', '=', ano_verificacao),
                        ('state', 'in', ['done', 'verify']),
                    ]
                )
            else:
                # periodos_ferias_simulacao = \
                #     self.env['hr.vacation.control'].search(
                #         [
                #             ('contract_id', '=', self.contract_id.id),
                #             ('inicio_gozo', '=', data_inicio),
                #             ('fim_gozo', '=', data_fim)
                #         ]
                #     )
                domain = [
                    ('tipo_de_folha', '=', tipo_simulacao),
                    ('is_simulacao', '=', True),
                    ('mes_do_ano', '=', mes_verificacao),
                    ('ano', '=', ano_verificacao),
                    ('state', 'in', ['done', 'verify']),
                ]

                domain.append(
                    ('periodo_aquisitivo', '=',
                     self.contract_id.vacation_control_ids[0].id if
                     not ferias_vencida else
                     self.contract_id.vacation_control_ids[1].id)
                )
                payslip_simulacao = self.env['hr.payslip'].search(domain)
        else:
            # periodos_ferias_simulacao = \
            #     self.env['hr.vacation.control'].search(
            #         [
            #             ('contract_id', '=', self.contract_id.id),
            #             ('inicio_gozo', '=', data_inicio),
            #             ('fim_gozo', '=', data_fim)
            #         ]
            #     )
            domain = [
                ('tipo_de_folha', '=', tipo_simulacao),
                ('is_simulacao', '=', True),
                ('mes_do_ano', '=', mes_verificacao),
                ('ano', '=', ano_verificacao),
                ('state', 'in', ['done', 'verify']),
            ]
            domain.append(
                ('periodo_aquisitivo', '=',
                 self.contract_id.vacation_control_ids[0].id if
                 not ferias_vencida else
                 self.contract_id.vacation_control_ids[1].id)
            )
            payslip_simulacao = self.env['hr.payslip'].search(domain)
        if len(payslip_simulacao) > 1:
            #
            # Excluir as simulações existentes para forçar uma nova
            #
            for payslip in payslip_simulacao:
                payslip.unlink()
            # raise exceptions.Warning(
            #    _(
            #        'Existem duas simulações '
            #        'para %s neste período' % tipo_simulacao
            #    )
            # )
            payslip_simulacao = self.env['hr.payslip'].search(domain)

        if len(payslip_simulacao) == 0:
            payslip_simulacao_criada = self.gerar_simulacao(
                tipo_simulacao, mes_verificacao,
                ano_verificacao, data_inicio,
                data_fim, ferias_vencida=ferias_vencida
            )
            return self._buscar_valor_bruto_simulacao(
                payslip_simulacao_criada, um_terco_ferias)
        else:
            return self._buscar_valor_bruto_simulacao(
                payslip_simulacao, um_terco_ferias)

    # @api.multi
    # def buscar_media_rubrica(self, rubrica_id):
    #     rubrica = self.env['hr.salary.rule'].browse(rubrica_id)
    #     for media in self.medias_proventos:
    #         if rubrica.name == media.nome_rubrica:
    #             return media.media

    @profile
    @api.multi
    def verificar_adiantamento_13_aviso_ferias(self):
        """
        Verifica se houve aidantamento de 13º salário no aviso de férias do
        periodo
        :return: Retorna a linha do adiantamento de 13º existente no aviso
        de férias
        """
        payslips_id = self.search(
            [
                ('tipo_de_folha', '=', 'ferias'),
                ('contract_id', '=', self.contract_id.id),
                ('date_from', '>=', str(self.ano) + '-01-01'),
                ('date_to', '<=', self.date_to),
                ('state', 'in', ['done', 'verify']),
                ('is_simulacao', '=', False),
            ]
        )
        salary_rule_id = self.env['hr.salary.rule'].search(
            [
                ('code', '=', 'ADIANTAMENTO_13')
            ]
        )
        payslip_line_id = self.env['hr.payslip.line'].search(
            [
                ('slip_id', 'in', payslips_id.ids),
                ('salary_rule_id', '=', salary_rule_id.id),
            ]
        )
        return payslip_line_id

    @profile
    @api.multi
    def BUSCAR_ADIANTAMENTO_DECIMO_TERCEIRO(self):
        """
        Retorna o valor total do adiantamento de 13º pedido no aviso de férias
        :return: Valor total da linha do adiantamento do 13º no aviso de férias
        """
        payslip_line_id = self.verificar_adiantamento_13_aviso_ferias()
        return payslip_line_id.total

    @profile
    @api.multi
    def verificar_ferias_no_periodo(self):
        """
        Função responsável por procurar a férias parcial tirada no periodo
        atual referente ao último periodo vencido de férias. Calcular o valor
        total pago pelos dias de gozo e o 1/3 sobre este valor.
        :return: Total dos dias de gozo + 1/3 sobre o total dos dias de gozo
        """
        periodo_aquisitivo = self._verificar_ferias_vencidas()
        payslip_ferias = self.search(
            [
                ('tipo_de_folha', '=', 'ferias'),
                ('holidays_ferias', '!=', False),
                ('contract_id', '=', self.contract_id.id),
                ('date_from', '>=', periodo_aquisitivo.inicio_concessivo),
                ('date_to', '<=', periodo_aquisitivo.fim_concessivo),
            ]
        )
        total = 0.0
        for line in payslip_ferias.line_ids:
            if line.salary_rule_id.code == "FERIAS":
                total += line.total
            elif line.salary_rule_id.code == "1/3_FERIAS":
                total += line.total
        return total

    @profile
    @api.multi
    def BUSCAR_ADIANTAMENTO_FERIAS(self):
        """
        Função chamada pela rúbrica Adiantamento de Férias para buscar o valor
        das férias parciais que foi tirada no periodo pelo funcionario.
        :return: Total pago na férias parcial do periodo
        """
        return self.verificar_ferias_no_periodo()

    @profile
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
        return 0

    @profile
    def get_reference(self, competencia='atual'):
        """
        Definir referência da Rubrica
        :return: str - referência ('AAAA-MM')
        """
        if competencia == 'atual':
            referencia = self.date_from[:7]
        else:
            competencia_atual = fields.Datetime.from_string(self.date_from)
            competencia_seguinte = competencia_atual + relativedelta(months=1)
            referencia = str(competencia_seguinte.date())[:7]
        referencia = '{}-{}'.format(referencia[-2:], referencia[:4])
        return referencia

    @profile
    def get_hr_payslip_line_by_code(self, code, reference):
        """
        Buscar linha calculada do holerite
        :param code: str - Código da rubrica
        :param reference: str referencia da rubrica
        :return: float - valor da rubrica processada
        """
        domain = [
            ('contract_id', '=', self.contract_id.id),
            ('code', 'ilike', '%{}%'.format(code)),
            ('reference', '=', reference),
            ('slip_id.is_simulacao', '=', False),
        ]

        if self.tipo_de_folha == 'normal':
            domain.append(('slip_id.tipo_de_folha', '=', 'ferias'))
        else:
            domain.append(
                ('slip_id.tipo_de_folha', 'not in',
                 ['provisao_ferias', 'provisao_decimo_terceiro']))

        line_ids = self.env['hr.payslip.line'].search(domain)
        return sum(line_ids.mapped('total'))

    @profile
    def get_inss_ferias_da_competencia(self, reference):
        """
        Buscar o valor de INSS pago na competencia que vier nos parâmetros
        """
        reference_mes = int(reference[:2])
        reference_ano = int(reference[-4:])

        # Tratar o mes de janeiro que devera buscar apartir do mes de dezembro
        if reference_mes == 1:
            mes_inicial = 12
            ano_inicial = reference_ano - 1
        else:
            mes_inicial = reference_mes - 1
            ano_inicial = reference_ano

        mes_final = reference_mes + 1
        if mes_final >= 12:
            mes_final = 1
            reference_ano += 1

        data_inicial = '{}-{}-01'.format(ano_inicial, mes_inicial)
        data_final = '{}-{}-01'.format(reference_ano, mes_final)

        domain = [
            ('tipo_de_folha', 'in', ['ferias']),
            ('contract_id', '=', self.contract_id.id),
            ('state', 'in', ['done', 'verify']),
            ('date_from', '>=', data_inicial),
            ('date_from', '<=', data_final),
            ('is_simulacao', '=', False),
        ]
        holerite_ferias_id = self.search(
            domain, limit=1, order='date_from DESC')

        # Se não localizar nenhuma férias retorna 0
        if not holerite_ferias_id:
            return 0

        # Se o mes da referencia for o mesmo das ferias encontradas,
        # retornar a rubrica de INSS_COMPETENCIA_ATUAL
        if holerite_ferias_id.mes_do_ano == reference_mes:
            return holerite_ferias_id[0].line_ids.filtered(
                lambda x: x.code == 'INSS_COMPETENCIA_ATUAL').total or 0.0

        if holerite_ferias_id.mes_do_ano == (reference_mes - 1):
            return holerite_ferias_id[0].line_ids.filtered(
                lambda x: x.code == 'INSS_COMPETENCIA_SEGUINTE').total or 0.0

        return 0.0

    @profile
    def busca_adiantamento_13(self):
        '''Metodo para recuperar valor pago de adiantamento de 13º no ano
        :return:     float - Valor pago neste ano
        '''
        domain = [
            ('tipo_de_folha', 'in', ['decimo_terceiro', 'ferias']),
            ('contract_id', '=', self.contract_id.id),
            ('state', 'in', ['done', 'verify']),
            ('ano', '=', self.ano),
            ('is_simulacao', '=', False),
            ('mes_do_ano', '<=', self.mes_do_ano),
        ]
        holerites = self.search(domain, order='mes_do_ano DESC')

        valor = 0
        if holerites:
            for holerite in holerites:
                for line in holerite.line_ids:
                    if line.code in [
                        'ADIANTAMENTO_13',
                        'ADIANTAMENTO_13_FERIAS',
                        'PRIMEIRA_PARCELA_13',
                    ]:
                        if not (self.tipo_de_folha == 'ferias'
                                and holerite.mes_do_ano == self.mes_do_ano):
                            valor += line.total

            # PAra contratos de PSS temos a rubrica de desconto de adiantamento do cedido
            # como é uma rubrica de deducao, diminuir o valor caso a encontre
            if holerite.contract_id.adiantamento_13_cedente:

                # Buscar nos holerites de primeira parcela se ja foi descontado
                desconto_line_id = \
                    holerites.mapped('line_ids').filtered(
                        lambda x: x.code == 'ADIANTAMENTO_13_CEDIDO')

                if desconto_line_id:
                    valor -= desconto_line_id.total or 0
        return valor

        # caso nao encontre holerite de adiantamento,
        # retorne o valor cadastrado no contrato
        # return self.contract_id.adiantamento_13_cedente or 0.0

    @profile
    def rubrica_anterior_total(self, code, mes=-1, tipo_de_folha='normal'):
        '''Metodo para recuperar uma rubrica de um mes anterior
        :param code:  string -   Code de identificação da rubrica
        :param meses: int [1-12] Identificar um mes especifico
                            -1   Selecionar o ultimo payslip calculado
        :param tipo_de_folha:
        :return:
        '''
        domain = [
            ('tipo_de_folha', '=', tipo_de_folha),
            ('contract_id', '=', self.contract_id.id),
            ('is_simulacao', '=', False),
            ('state', 'in', ['done', 'verify'])
        ]

        # Calcula mes_anterior
        anos = [self.ano]
        mes_anterior = self.mes_do_ano - 1
        if mes_anterior == 0:
            mes_anterior = 12
            anos.append(self.ano - 1)

        if mes and mes > 0:
            domain.append(('mes_do_ano', '=', mes))

        if mes == -1 and tipo_de_folha == 'ferias':
            domain.append(('mes_do_ano', 'in',
                           [self.mes_do_ano, mes_anterior]))

        domain.append(('ano', 'in', anos))

        holerite = self.search(domain, order='date_from DESC', limit=1)

        if holerite and self.tipo_de_folha in ['rescisao', 'decimo_terceiro']:
            return sum(
                holerite.line_ids.filtered(lambda x: x.code == code).mapped(
                    'total')) or 0.0

        valores = 0
        if holerite:
            if (self.date_from <= holerite.date_from <= self.date_to or
                    self.date_from <= holerite.date_to <= self.date_to):
                for line in holerite.line_ids:
                    if line.code == code:
                        valores += line.total

        return valores

    @profile
    def rubrica_pensao_alimentar(self):
        '''
        :param code:  string -   Code de identificação da rubrica
        :param meses: int [1-12] Identificar um mes especifico
                            -1   Selecionar o ultimo payslip calculado
        :param tipo_de_folha:
        :return:
        '''

        domain = [
            ('tipo_de_folha', '=', 'ferias'),
            ('contract_id', '=', self.contract_id.id),
            ('is_simulacao', '=', False),
            ('state', 'in', ['done', 'verify'])
        ]

        # Calcula mes_anterior
        anos = [self.ano]
        mes_anterior = self.mes_do_ano - 1
        if mes_anterior == 0:
            mes_anterior = 12
            anos.append(self.ano - 1)

        if self.mes_do_ano and mes_anterior > 0:
            domain.append(('mes_do_ano', 'in', [self.mes_do_ano, mes_anterior]))

        if mes_anterior == -1:
            domain.append(('mes_do_ano', 'in',
                           [self.mes_do_ano, mes_anterior]))
            domain.append(('ano', 'in', anos))

        holerite = self.search(domain, order='create_date DESC', limit=1)

        valores = 0

        if holerite:
            if self.date_from <= holerite.date_from <= self.date_to or \
                    self.date_from <= holerite.date_to <= self.date_to:
                for line in holerite.line_ids:
                    if line.code == 'PENSAO_ALIMENTICIA':
                        valores += line.total
        return valores

    @profile
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

        # Construir um browsableObject para informações da quantidade de dias
        # de ferias e de abono na payslip.
        #     payslip.holidays_ferias
        dias_abono_ferias = {}
        if payslip.holidays_ferias and not payslip.is_simulacao:
            if payslip.holidays_ferias.vacations_days:
                dias_abono_ferias.update(
                    {'DIAS_FERIAS': payslip.holidays_ferias.vacations_days}
                )
            if payslip.holidays_ferias.sold_vacations_days:
                dias_abono_ferias.update(
                    {'DIAS_ABONO': payslip.holidays_ferias.sold_vacations_days}
                )
        elif payslip.struct_id.code == "FERIAS" and payslip.is_simulacao:
            if not payslip.saldo_periodo_aquisitivo:
                dias_abono_ferias.update({
                    'DIAS_FERIAS': worked_days[u'SALDO_FERIAS'].number_of_days
                })
            else:
                dias_abono_ferias.update(
                    {'DIAS_FERIAS': payslip.saldo_periodo_aquisitivo}
                )
        else:
            dias_abono_ferias.update(
                {'DIAS_FERIAS': payslip.saldo_periodo_aquisitivo}
            )
        ferias_abono = InputLine(payslip.employee_id.id, dias_abono_ferias)

        # Variavel para contabilizar os avos na contabilização do
        # adiantamento do decimo terceiro salario
        adiantamento_avos_13 = 6

        #
        # Calcula os Avos do payslip para Provisão de 13º Salário
        #

        # Ajusta para casos que mes = 13 representando decimo terceiro salario
        mes_do_ano = payslip.mes_do_ano if payslip.mes_do_ano < 12 else 12

        # Se a data de contratação for no ano corrente,
        # a variavel que indica a quantidade de meses de 13 salario
        # deve ser contabilizada a partir da data de contratação
        # exemplo.:
        # Data Corrente: 01/12/2017
        # contratação: 31/05/2017 -> avos_13 = (mescorrente - 05) -1  = 6
        # contratação: 31/05/2016 -> avos_13 = mes corrente -1 = 11
        if fields.Date.from_string(payslip.contract_id.date_start) > \
                fields.Date.from_string(str(payslip.ano) + '-01-01'):

            dia_inicio_contrato = \
                fields.Date.from_string(payslip.contract_id.date_start).day
            mes_inicio_contrato = \
                fields.Date.from_string(payslip.contract_id.date_start).month

            avos_13 = int(mes_do_ano) - int(mes_inicio_contrato) + 1

            adiantamento_avos_13 = 7 - int(mes_inicio_contrato)

            # Se trabalhou mais do que 15 dias no mes, contar o mes nos avos
            # de adiantamento de 13 salario. Senao trabalhou pelo menos 15
            # dias na data de contratacao, diminuir um avo da contabilidade dos avos
            ultimo_dia = fields.Date.from_string(
                payslip.contract_id.date_end).day if payslip.contract_id.date_end else ultimo_dia_mes(
                payslip.contract_id.date_start).day
            if not ultimo_dia - dia_inicio_contrato + 1 >= 15:
                avos_13 -= 1
                adiantamento_avos_13 -= 1
        else:
            avos_13 = mes_do_ano

        # No contrato do PSS, o calculo do 13 Salario é diferente.
        # mesmo que a data de contratação for no ano corrente,
        # contabilizar todos os meses do ano.
        # exemplo.:
        # Data Corrente: 01/12/2017
        # contratação: 31/11/2017 -> avos_13 = 12
        # contratação: 31/05/2017 -> avos_13 = 12
        # contratação: 31/05/2016 -> avos_13 = 12
        if payslip.contract_id.data_admissao_cedente:
            avos_13 = mes_do_ano

        # Quando ja existir data final no contrato (rescisao) ou
        # for uma simulacao com data de afastamento
        if payslip.contract_id.date_end or payslip.data_afastamento:

            if payslip.contract_id.date_end:
                data_final = \
                    datetime.strptime(payslip.contract_id.date_end, '%Y-%m-%d')

            if payslip.data_afastamento:
                data_final = \
                    datetime.strptime(payslip.data_afastamento, '%Y-%m-%d')
                data_final += relativedelta(days=-1)

            if data_final.month == mes_do_ano:

                dia_fim_contrato = data_final.day

                if dia_fim_contrato < 15:

                    avos_13 -= 1
        #
        # Quando for rescisao, verificar se ja foi calculado o holerite do mes.
        # Por exemplo, a folha eh processado em 17/05 e no dia 30/05 acontece
        # uma rescisao. nesse caso devemos deduzir os dias pagos no holerite
        # normal ao funcionario.
        DIAS_A_MAIOR = 0

        if payslip.tipo_de_folha == 'rescisao':

            # verificar se ja foi gerado o holerite do mes
            holerite_id = self.search([
                ('contract_id', '=', payslip.contract_id.id),
                ('is_simulacao', '=', False),
                ('tipo_de_folha', '=', 'normal'),
                ('mes_do_ano2', '=', payslip.mes_do_ano2),
                ('ano', '=', payslip.ano),
                ('state', 'in', ['done', 'verify']),
            ])

            # Seta todos na mesma data para nao calcular nenhum dia de saldo de
            # salario, visto que ja foi calculado no holerite normal
            if holerite_id:
                payslip.date_from = payslip.data_afastamento
                payslip.date_to = payslip.data_afastamento

                ultimo_dia_trabalhado = \
                    fields.Date.from_string(payslip.data_afastamento).day - 1
                ultimo_dia_holerite_normal = \
                    fields.Date.from_string(holerite_id.date_to).day

                # Dias que deverão ser descontado do funcionario
                DIAS_A_MAIOR = ultimo_dia_holerite_normal - ultimo_dia_trabalhado

        baselocaldict = {
            'CALCULAR': payslip, 'BASE_INSS': 0.0, 'BASE_FGTS': 0.0,
            'BASE_IR': 0.0, 'categories': categories_obj, 'rules': rules_obj,
            'payslip': payslip_obj, 'worked_days': worked_days_obj,
            'inputs': input_obj, 'rubrica': None, 'SALARIO_MES': salario_mes,
            'SALARIO_DIA': salario_dia, 'SALARIO_HORA': salario_hora,
            'RAT_FAP': rat_fap, 'MEDIAS': medias_obj,
            'PEDIDO_FERIAS': ferias_abono, 'PAGAR_FERIAS': False,
            'AVOS_13': avos_13, 'adiantamento_avos_13': adiantamento_avos_13,
            'DIAS_AVISO_PREVIO': payslip.dias_aviso_previo,
            'RUBRICAS_ESPEC_CALCULADAS': [],
            'locals': locals,
            'globals': locals,
            'Decimal': Decimal,
            'D': Decimal,
            'DIAS_A_MAIOR': DIAS_A_MAIOR,
        }

        # recuperar todas as estrututras que serao processadas
        # (estruturas da payslip atual e as estruturas pai da payslip)
        structure_ids = payslip.struct_id._get_parent_structure()

        # recuperar as regras das estruturas e filha de cada regra
        rule_ids = self.env['hr.payroll.structure'].browse(
            structure_ids).get_all_rules()

        applied_specific_rule = defaultdict(list)

        payslip.get_contract_specific_rubrics(
            applied_specific_rule, rule_ids, DIAS_A_MAIOR)

        # Buscar informações de férias dentro do mês que esta sendo
        # processado. Isto é, fazer uma busca para verificar se no mês de
        # outubro o funcionário ja gozou alguma férias.
        lines, holidays_ferias = self.buscar_ferias_do_mes(payslip)
        # Se encontrar informações de férias gozadas dentro do mês,
        #  trazer as informações de férias para o holerite mensal.
        if holidays_ferias and worked_days_obj.FERIAS.number_of_days > 0 \
                and payslip.tipo_de_folha == 'normal':
            # Atualiza o Holerite para colocar o holidays_ferias correspondente
            self.env['hr.payslip'].browse(
                payslip_id).holidays_ferias = holidays_ferias
            # Atualizar o baselocaldict para informar que tem que pagar
            # ferias naquele holerite
            baselocaldict.update({'PAGAR_FERIAS': True})
            # Recuperar configurações do RH para calcular férias proporcio
            ferias_proporcionais = \
                self.env['ir.config_parameter'].get_param(
                    'l10n_br_hr_payroll_ferias_proporcionais',
                    default=False)

            if ferias_proporcionais:
                proporcao_ferias = \
                    worked_days_obj.FERIAS.number_of_days / \
                    holidays_ferias.vacations_days

                if holidays_ferias.sold_vacations_days == 0:
                    proporcao_abono = 0
                else:
                    proporcao_abono = \
                        worked_days_obj.ABONO_PECUNIARIO.number_of_days / \
                        holidays_ferias.sold_vacations_days

            for line in lines:
                key = line.code + '_FERIAS'
                amount = line.amount
                qty = line.quantity
                category_id = line.category_id
                name = line.name

                if ferias_proporcionais:
                    if line.code in \
                            ['ABONO_PECUNIARIO', '1/3_ABONO_PECUNIARIO']:
                        qty *= proporcao_abono
                    else:
                        qty *= proporcao_ferias

                if 'FERIAS' not in line.code:
                    name += u' (Férias)'

                result_dict[key] = {
                    'salary_rule_id': line.salary_rule_id.id,
                    'contract_id': payslip.contract_id.id,
                    'name': name,
                    'reference': line.reference,
                    'code': line.code + '_FERIAS',
                    'category_id': category_id.id,
                    'sequence': line.sequence - 0.01,
                    'appears_on_payslip': line.appears_on_payslip,
                    'condition_select': line.condition_select,
                    'condition_python': line.condition_python,
                    'condition_range': line.condition_range,
                    'condition_range_min': line.condition_range_min,
                    'condition_range_max': line.condition_range_max,
                    'amount_select': line.amount_select,
                    'amount_fix': line.amount_fix,
                    'amount_python_compute':
                        line.amount_python_compute,
                    'amount_percentage': line.amount_percentage,
                    'amount_percentage_base':
                        line.amount_percentage_base,
                    'register_id': line.register_id.id,
                    'amount': amount,
                    'employee_id': payslip.employee_id.id,
                    'quantity': qty,
                    'rate': line.rate,
                    'partner_id': line.partner_id.id,
                }
                baselocaldict[line.code + '_FERIAS'] = line.total

                # sum the amount for its salary category
                baselocaldict = _sum_salary_rule_category(
                    baselocaldict, line.category_id,
                    line.total)

                if line.category_id.code == 'DEDUCAO':
                    if line.salary_rule_id.compoe_base_INSS:
                        baselocaldict['BASE_INSS'] -= line.total
                    if line.salary_rule_id.compoe_base_IR:
                        baselocaldict['BASE_IR'] -= line.total
                    if line.salary_rule_id.compoe_base_FGTS:
                        baselocaldict['BASE_FGTS'] -= line.total
                else:
                    if line.salary_rule_id.compoe_base_INSS:
                        baselocaldict['BASE_INSS'] += line.total
                    if line.salary_rule_id.compoe_base_IR:
                        baselocaldict['BASE_IR'] += line.total
                    if line.salary_rule_id.compoe_base_FGTS:
                        baselocaldict['BASE_FGTS'] += line.total

                # Cria ajuste de INSS (Provento) proporcional às ferias
                # Como ja foi pago o INSS no aviso de ferias, É criado
                # uma rubrica de provento para devolver ao funcionario
                # o valor descontado nas ferias proporcionalmente a
                #  competencia corrente.
                # if line.code == 'INSS':
                #    line.copy({
                #        'slip_id': payslip.id,
                #        'name': line.name + ' (ferias)',
                #        'code': 'AJUSTE_' + line.code + '_FERIAS',
                #        'sequence': 199,
                #    })
                #    name = u'Ajuste INSS Férias'
                #    category_id = \
                #        self.env.ref('hr_payroll.PROVENTO')
                #    # Ajuste do INSS compoe base do IR
                #    # mas nao compoe base do INSS
                #    baselocaldict['BASE_INSS'] -= line.total
                #    baselocaldict['BASE_IR'] += line.total

        # organizando as regras pela sequencia de execução definida
        sorted_rule_ids = \
            [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]

        # organizando as regras especificas pela ordem definida

        if payslip.tipo_de_folha == "rescisao":
            if not payslip.verificar_adiantamento_13_aviso_ferias():
                salary_rule_id = self.env['hr.salary.rule'].search(
                    [
                        ('code', '=', 'ADIANTAMENTO_13_RESC'),
                    ]
                )
                if salary_rule_id.id in sorted_rule_ids:
                    sorted_rule_ids.remove(salary_rule_id.id)
            if not payslip._verificar_ferias_vencidas():
                ferias_vencida_rubrica = self.env['hr.salary.rule'].search(
                    [
                        ('code', '=', 'FERIAS_VENCIDAS'),
                    ]
                )
                sorted_rule_ids.remove(ferias_vencida_rubrica.id)
                ferias_vencida_1_3_rubrica = \
                    self.env['hr.salary.rule'].search(
                        [
                            ('code', '=', 'FERIAS_VENCIDAS_1/3')
                        ]
                    )
                sorted_rule_ids.remove(ferias_vencida_1_3_rubrica.id)
                adiantamento_ferias_vencida = \
                    self.env['hr.salary.rule'].search(
                        [
                            ('code', '=', 'ADIANTAMENTO_FERIAS_RESC')
                        ]
                    )
                sorted_rule_ids.remove(adiantamento_ferias_vencida.id)
            if not payslip.dias_aviso_previo:
                aviso_previo_indenizado = \
                    self.env['hr.salary.rule'].search(
                        [
                            ('code', '=', 'AVISO_PREV_IND')
                        ]
                    )
                ferias_aviso_previo = \
                    self.env['hr.salary.rule'].search(
                        [
                            ('code', '=', 'PROP_FERIAS_AVISO_PREVIO')
                        ]
                    )
                ferias_1_3_aviso_previo = \
                    self.env['hr.salary.rule'].search(
                        [
                            ('code', '=', 'PROP_1/3_FERIAS_AVISO_PREVIO')
                        ]
                    )
                if aviso_previo_indenizado:
                    sorted_rule_ids.remove(aviso_previo_indenizado.id)
                if ferias_aviso_previo:
                    sorted_rule_ids.remove(ferias_aviso_previo.id)
                if ferias_1_3_aviso_previo:
                    sorted_rule_ids.remove(ferias_1_3_aviso_previo.id)

        employee = payslip.contract_id.employee_id
        localdict = dict(
            baselocaldict, employee=employee, contract=payslip.contract_id)

        references = defaultdict(list)

        for rule in obj_rule.browse(sorted_rule_ids):
            localdict['result'] = None
            localdict['result_qty'] = 1.0
            localdict['result_rate'] = 100
            localdict['rubrica'] = rule
            localdict['reference'] = ' '
            beneficiario_id = False
            ref = False
            amount = False
            qty = False
            rate = False

            # check if the rule can be applied
            if not (rule.id in applied_specific_rule or \
                    obj_rule.satisfy_condition(rule.id, localdict)):
                continue

            # compute the amount of the rule
            if rule.id in applied_specific_rule and \
                    rule.code not in CALCULATED_SPECIFC_RULE:

                lista_rubricas_especificas = applied_specific_rule[rule.id]

                # Verifica quais rúbricas especificas devem ser aplicadas
                for specific_item in lista_rubricas_especificas:
                    #
                    # Aplicando regra do benecicio;
                    #
                    if (specific_item.get('type') == u'benefit'and not (
                            specific_item.get('ref') and
                            specific_item['ref'] in references.get(rule.id, []))):

                        amount, qty, rate, ref = specific_item['value']

                        del lista_rubricas_especificas[0]
                        applied_specific_rule[rule.id] = \
                            lista_rubricas_especificas

                        break
                    #
                    # Aplicando regra especifica do contrato
                    #
                    elif (specific_item.get('type') == u'contract' and not (
                            specific_item.get('ref') and
                            specific_item['ref'] in references.get(rule.id, []))):
                        amount, qty, rate, ref = specific_item['value']

                        del lista_rubricas_especificas[0]
                        applied_specific_rule[rule.id] = \
                            lista_rubricas_especificas

                        break

            else:
                amount, qty, rate = \
                    obj_rule.compute_rule(rule.id, localdict)

                # Pegar Referencia que irá para o holerite
                ref = obj_rule.get_reference_rubrica(
                    rule.id, localdict
                )

            references[rule.id].append(ref)
                        if rule.compoe_base_INSS:
                            localdict['BASE_INSS'] += tot_rule
                        if rule.compoe_base_IR:
                            localdict['BASE_IR'] += tot_rule
                        if rule.compoe_base_FGTS:
                            localdict['BASE_FGTS'] += tot_rule

            # check if there is already a rule computed
            # with that code
            previous_amount = \
                rule.code in localdict and \
                localdict[rule.code] or 0.0
            # previous_amount = 0
            # set/overwrite the amount computed
            # for this rule in the localdict

            tot_rule = Decimal(amount or 0) * Decimal(
                qty or 0) * Decimal(rate or 0) / 100.0
            tot_rule = tot_rule.quantize(Decimal('0.01'))
            if localdict.get(rule.code) and \
                    rule.category_id.code == 'PROVENTO':
                localdict[rule.code] += tot_rule
            else:
                localdict[rule.code] = tot_rule

            if rules.get(rule.code) and rule.category_id.code == 'PROVENTO':
                rules[rule.code] += rule
            else:
                rules[rule.code] = rule

            # sum the amount for its salary category
            localdict = _sum_salary_rule_category(
                localdict, rule.category_id,
                tot_rule)

            # Verificar se a rubrica esta nas rubricas especificas
            if applied_specific_rule.get(rule.id):
                beneficiario_id = applied_specific_rule.get(rule.id)[0]\
                    .get('beneficiario_id')

            # create/overwrite the rule in the temporary results
            result_dict[random.randint(0, 10000)] = {
                'salary_rule_id': rule.id,
                'contract_id': payslip.contract_id.id,
                'name': rule.name,
                'code': rule.code,
                'category_id': rule.category_id.id,
                'sequence': rule.sequence,
                'appears_on_payslip': rule.appears_on_payslip,
                'condition_select': rule.condition_select,
                'condition_python': rule.condition_python,
                'condition_range': rule.condition_range,
                'condition_range_min':
                    rule.condition_range_min,
                'condition_range_max':
                    rule.condition_range_max,
                'amount_select': rule.amount_select,
                'amount_fix': rule.amount_fix,
                'amount_python_compute':
                    rule.amount_python_compute,
                'amount_percentage': rule.amount_percentage,
                'amount_percentage_base':
                    rule.amount_percentage_base,
                'register_id': rule.register_id.id,
                'amount': amount,
                'employee_id': payslip.contract_id.employee_id.id,
                'quantity': qty,
                'rate': rate,
                'reference': ref or '',
                'partner_id':
                    beneficiario_id and beneficiario_id.id or
                    payslip.contract_id.employee_id.address_home_id and
                    payslip.contract_id.employee_id.address_home_id.id or
                    False,
            }

            if rule.category_id.code == 'DEDUCAO':
                if rule.compoe_base_INSS:
                    localdict['BASE_INSS'] -= tot_rule
                if rule.compoe_base_IR:
                    localdict['BASE_IR'] -= tot_rule
                if rule.compoe_base_FGTS:
                    localdict['BASE_FGTS'] -= tot_rule
            else:
                if rule.compoe_base_INSS:
                    localdict['BASE_INSS'] += tot_rule
                if rule.compoe_base_IR:
                    localdict['BASE_IR'] += tot_rule
                if rule.compoe_base_FGTS:
                    localdict['BASE_FGTS'] += tot_rule

        result = [value for code, value in result_dict.items()]
        return result

    @profile
    def atualizar_worked_days_inputs(self):
        """
        Atualizar os campos worked_days_line_ids e input_line_ids do holerite.
        Com os campos de contrato, employee, date_from e date_to do holerite
        ja setados, esse metodo exclui as variaveis base para calculo do
        holerite e os instancia novamente atualizando os valore.
        :return: Campos atualizados
        """
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
        # computation of the salary input
        self.worked_days_line_ids = self.get_worked_day_lines(
            self.contract_id.id, self.date_from, self.date_to
        )
        self.input_line_ids = self.get_inputs(
            self.contract_id.id, self.date_from, self.date_to
        )

    @api.multi
    @api.depends('contract_id', 'mes_do_ano')
    def _compute_set_employee_id(self):
        for record in self:
            record.struct_id = record.buscar_estruturas_salario()
            if record.contract_id:
                record.employee_id = record.contract_id.employee_id
                record.company_id = record.contract_id.company_id
                record.salary_unit_code = record.contract_id.salary_unit.code
                record.valor_tarefa = record.contract_id.wage

    def _compute_data_mes_ano(self):
        for record in self:
            record.data_mes_ano = MES_DO_ANO[record.mes_do_ano - 1][1][:3] + \
                                  '/' + str(record.ano)

    # @api.depends('mes_do_ano', 'ano', 'holidays_ferias', 'data_afastamento')
    @api.multi
    @api.onchange('mes_do_ano', 'ano', 'data_afastamento', 'date_from',
                  'date_to', 'holidays_ferias')
    def _compute_set_dates(self):
        for record in self:
            if not record.mes_do_ano:
                record.mes_do_ano = datetime.now().month
                record.mes_do_ano2 = datetime.now().month
            if record.tipo_de_folha == 'ferias' and record.holidays_ferias:
                if record.holidays_ferias.parent_id.controle_ferias_ids:
                    record.periodo_aquisitivo = \
                        record.holidays_ferias.parent_id.controle_ferias_ids[0]
                record.date_from = record.holidays_ferias.data_inicio
                record.date_to = record.holidays_ferias.data_fim
                record.mes_do_ano = \
                    datetime.strptime(record.date_from, '%Y-%m-%d').month
                record.ano = \
                    datetime.strptime(record.date_from, '%Y-%m-%d').year
                continue
            if record.tipo_de_folha == 'provisao_ferias':
                continue

            mes = record.mes_do_ano
            if mes > 12:
                mes = 12

            ultimo_dia_do_mes = str(
                self.env['resource.calendar'].get_ultimo_dia_mes(
                    mes, record.ano))

            primeiro_dia_do_mes = str(
                datetime.strptime(str(mes) + '-' +
                                  str(record.ano), '%m-%Y'))

            record.date_from = primeiro_dia_do_mes
            record.date_to = ultimo_dia_do_mes

            data_de_inicio = record.contract_id.date_start
            data_final = record.contract_id.date_end

            if data_de_inicio and primeiro_dia_do_mes < data_de_inicio:
                record.date_from = record.contract_id.date_start

            if data_final and record.tipo_de_folha == 'rescisao' and \
                    ultimo_dia_do_mes > data_final:
                record.date_to = record.contract_id.date_end

            #
            # validacoes abaixo daqui sopmente para casos de rescisoa
            #
            if record.tipo_de_folha != 'rescisao':
                return

            if record.data_afastamento and record.data_afastamento < ultimo_dia_do_mes and not record.data_afastamento == primeiro_dia_do_mes[
                                                                                                                          :10]:
                record.date_to = \
                    fields.Date.from_string(record.data_afastamento) - \
                    timedelta(days=1)
            # Afastamento no primeiro dia do mes,calcular apenas a rescisao.
            # Outros calculos ficarao no holerite normal do mes anterior
            if record.data_afastamento == primeiro_dia_do_mes[:10]:
                record.date_to = primeiro_dia_do_mes

            # verificar se ja foi gerado o holerite do mes
            holerite_id = self.search([
                ('contract_id', '=', self.contract_id.id),
                ('is_simulacao', '=', False),
                ('tipo_de_folha', '=', 'normal'),
                ('mes_do_ano2', '=', record.mes_do_ano2),
                ('ano', '=', record.ano),
                ('state', 'in', ['done', 'verify']),
            ])

            if holerite_id:
                record.date_to = record.data_afastamento
                record.date_from = record.data_afastamento

    @profile
    @api.multi
    def _buscar_holerites_periodo_aquisitivo(self):
        if not self.periodo_aquisitivo:
            return False
        else:
            payslips = self.search([
                ('contract_id', '=', self.contract_id.id),
                ('date_from', '>=', self.periodo_aquisitivo.inicio_aquisitivo),
                ('date_to', '<=', self.periodo_aquisitivo.fim_aquisitivo),
                ('tipo_de_folha', '=', 'normal'),
                ('state', 'in', ['done', 'verify']),
            ])
            return payslips

    @profile
    @api.multi
    def _checar_holerites_aprovados(self):
        return self.search([
            ('contract_id', '=', self.contract_id.id),
            ('tipo_de_folha', '=', 'normal'),
            ('state', 'in', ['done', 'verify'])
        ])

    @api.multi
    def compute_sheet(self):
        for record in self:
            clear_prof_data()
            record._compute_sheet()
            log_prof_data()
            clear_prof_data()

    @profile
    @api.multi
    def _compute_sheet(self):
        self.ensure_one()

        if self.tipo_de_folha == "rescisao":

            # Excluir todas as simulações pré-existentes referentes a esta
            # Rescisão
            #
            simulacoes = self.env['hr.payslip'].search([
                ('contract_id', '=', self.contract_id.id),
                ('is_simulacao', '=', True),
                ('tipo_de_folha', '=', 'rescisao'),
            ])

            if simulacoes:
                simulacoes.state = 'draft'
                simulacoes.unlink()

        if self.tipo_de_folha in [
            "decimo_terceiro", "ferias", "aviso_previo",
            "provisao_ferias", "provisao_decimo_terceiro"
        ]:
            hr_medias_ids, data_de_inicio, data_final = \
                self.gerar_media_dos_proventos()

            if not self.tipo_de_folha == 'ferias' and not self. \
                    _buscar_holerites_periodo_aquisitivo():

                # Metodo pra validar se ja foram processadors
                # todos os holerites usados no calculo das medias
                # if self.tipo_de_folha in ["decimo_terceiro", "ferias"] and \
                if self.tipo_de_folha in ["decimo_terceiro"] and \
                        not self.is_simulacao:
                    self.validacao_holerites_anteriores(
                        data_de_inicio, data_final, self.contract_id)

                if self.tipo_de_folha == 'ferias':
                    if not self.holidays_ferias and not self.is_simulacao:
                        raise exceptions.Warning(
                            _('Nenhum Pedido de Ferias encontrado!')
                        )

                    # Validação da quantidade de dias de férias
                    # sendo processada e a quantidade de saldo dísponivel
                    if self.holidays_ferias.number_of_days_temp > \
                            self.saldo_periodo_aquisitivo:
                        raise exceptions.Warning(
                            _(u'Selecionado mais dias de ferias do que'
                              u'o saldo do periodo aquisitivo selecionado!')
                        )

        self.atualizar_worked_days_inputs()
        super(HrPayslip, self).compute_sheet()
        # self._compute_valor_total_folha()
        self._compute_rescisao_ids()
        return True

    @profile
    def _compute_rescisao_ids(self):
        self.rescisao_ids.unlink()
        rescisao_ids = []

        # Popula variáveis de descrição
        base = 0
        uteis = 0
        ferias = 0
        abono = 0
        trabalhado = 0
        avos = 0
        peraq = ''
        for variavel in self.worked_days_line_ids:
            if variavel.code == 'DIAS_BASE':
                base = variavel.number_of_days
            if variavel.code == 'DIAS_UTEIS':
                uteis = variavel.number_of_days
            if variavel.code == 'FERIAS':
                ferias = variavel.number_of_days
            if variavel.code == 'ABONO_PECUNIARIO':
                abono = variavel.number_of_days
            if variavel.code == 'DIAS_TRABALHADOS':
                trabalhado = variavel.number_of_days
        if self.ferias_vencidas:
            peraq = data.formata_data(
                self.ferias_vencidas.inicio_aquisitivo) + " a " + \
                    data.formata_data(self.ferias_vencidas.fim_aquisitivo)

        # Roda as linhas do holerite para popular as linhas de rescisão
        for line in self.line_ids:
            if line.salary_rule_id.campo_rescisao:
                codigo = line.salary_rule_id.campo_rescisao.codigo
                valor = line.total
                encontrou = False
                for item in rescisao_ids:
                    if item['codigo'] == codigo:
                        item['valor'] += valor
                        encontrou = True

                if not encontrou:

                    # Interpreta as variáveis na descrição
                    if self.contract_id.wage != 0.0:
                        avos = line['valor_provento'] / (
                                    self.contract_id.wage / 12)

                    name = line.salary_rule_id.campo_rescisao.descricao

                    descricao = Template(name).render(
                        DIAS_BASE="%d" % (base),
                        DIAS_UTEIS="%d" % (uteis),
                        FERIAS="%d" % (ferias),
                        ABONO_PECUNIARIO="%d" % (abono),
                        DIAS_TRABALHADOS="%d" % (trabalhado),
                        PERIODO_FERIAS_VENCIDAS=peraq,
                        AVOS="%d" % (int(round(avos, 2))))

                    tipo = line.salary_rule_id.category_id.code

                    # Rurica do INSS esta como referência por causa do e-social
                    if 'INSS' in line.code:
                        tipo = 'INSS'

                    rescisao_ids.append({
                        'codigo': codigo,
                        'name': descricao,
                        'valor': valor,
                        'tipo': tipo,
                    })
        self.rescisao_ids = rescisao_ids

    @profile
    def validacao_holerites_anteriores(self, data_inicio, data_fim, contrato):
        """
        VAlida se existe todos os holerites calculados e confirmados em
        determinado período.
        :param date_from:
        :param date_to:
        :return:
        """
        folha_obj = self.env['hr.payslip']
        domain = [
            ('date_from', '>=', data_inicio),
            ('date_from', '<=', data_fim),
            ('contract_id', '=', contrato.id),
            ('tipo_de_folha', '=', 'normal'),
            ('state', 'in', ['done', 'verify']),
        ]
        folhas_periodo = folha_obj.search(domain)

        folhas_sorted = folhas_periodo.sorted(key=lambda r: r.date_from)
        mes = fields.Datetime.from_string(data_inicio) + relativedelta(
            months=-1
        )
        mes_anterior = ''
        for folha in folhas_sorted:
            if mes_anterior and mes_anterior == folha.mes_do_ano:
                continue
            mes_anterior = folha.mes_do_ano
            mes = mes + relativedelta(months=1)
        #     if folha.mes_do_ano != mes.month:
        #         raise exceptions.ValidationError(
        #             _("Faltando Holerite confirmado do mês de %s de %s") %
        #             (MES_DO_ANO[mes.month - 1][1], mes.year))
        # if mes.month != fields.Datetime.from_string(data_fim).month:
        #     mes = fields.Datetime.from_string(data_fim).month
        #     raise exceptions.ValidationError(
        #         _("Não foi encontrado o último holerite do periodo "
        #           "aquisitivo, \nreferente ao mês  de %s de %s") %
        #         (MES_DO_ANO[mes - 1][1],
        #          fields.Datetime.from_string(data_fim).year))

    @profile
    @api.multi
    def gerar_media_dos_proventos(self):
        medias_obj = self.env['l10n_br.hr.medias']

        if self.tipo_de_folha in ['ferias', 'aviso_previo', 'provisao_ferias']:
            periodo_aquisitivo = self.periodo_aquisitivo
            data_de_inicio = \
                fields.Date.from_string(periodo_aquisitivo.inicio_aquisitivo)
            data_final = \
                fields.Date.from_string(periodo_aquisitivo.fim_aquisitivo)

            if self.tipo_de_folha in ['provisao_ferias']:
                data_final = \
                    '{}-{:02}-{:02}'.format(self.ano, self.mes_do_ano, 1)
                data_final = str(ultimo_dia_mes(data_final))

        elif self.tipo_de_folha in \
                ['decimo_terceiro', 'provisao_decimo_terceiro']:
            if self.contract_id.date_start > str(self.ano) + '-01-01':
                data_de_inicio = self.contract_id.date_start
            else:
                data_de_inicio = '{}-12-01'.format(self.ano - 1)
            data_final = self.date_to

        hr_medias_ids = medias_obj.gerar_media_dos_proventos(
            data_de_inicio, data_final, self)
        return hr_medias_ids, data_de_inicio, data_final

    @profile
    @api.model
    def BUSCAR_VALOR_MEDIA_PROVENTO(self, tipo_simulacao):
        # mes_verificacao, ano_verificacao, data_inicio, data_fim = \
        #    self._checar_datas_gerar_simulacoes(
        #        self.mes_do_ano, self.ano
        #    )
        mes_verificacao = self.mes_do_ano - 1
        if self.mes_do_ano == 1:
            mes_verificacao = 12
        ano_verificacao = self.ano
        if self.mes_do_ano == 1:
            ano_verificacao = self.ano - 1
        dias_no_mes = monthrange(ano_verificacao, mes_verificacao)
        data_inicio = str(ano_verificacao) + "-" + str(
            mes_verificacao) + "-" + "01"
        data_fim = str(ano_verificacao) + "-" + str(
            ano_verificacao) + "-" + str(dias_no_mes[1])
        if not tipo_simulacao == "ferias":
            payslip_simulacao = self.env['hr.payslip'].search(
                [
                    ('tipo_de_folha', '=', tipo_simulacao),
                    ('is_simulacao', '=', True),
                    ('mes_do_ano', '=', self.mes_do_ano),
                    ('ano', '=', ano_verificacao),
                    ('state', 'in', ['done', 'verify']),
                ]
            )
        else:
            periodos_ferias_simulacao = \
                self.env['hr.vacation.control'].search(
                    [
                        ('contract_id', '=', self.contract_id.id),
                        ('inicio_gozo', '=', data_inicio),
                        ('fim_gozo', '=', data_fim)
                    ]
                )
            payslip_simulacao = self.env['hr.payslip'].search(
                [
                    ('tipo_de_folha', '=', tipo_simulacao),
                    ('is_simulacao', '=', True),
                    ('mes_do_ano', '=', mes_verificacao),
                    ('ano', '=', ano_verificacao),
                    ('periodo_aquisitivo', '=',
                     periodos_ferias_simulacao[0].id),
                    ('state', 'in', ['done', 'verify']),
                ]
            )
        if not payslip_simulacao:
            payslip_simulacao_criada = self.gerar_simulacao(
                tipo_simulacao, mes_verificacao,
                ano_verificacao, data_inicio,
                data_fim, ferias_vencida=ferias_vencida
            )
            payslip_simulacao = payslip_simulacao_criada
        media_id = payslip_simulacao.medias_proventos[-1]
        return media_id.media / 12

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

    @profile
    def buscar_total_rubrica_payslip(self, codigo):
        """
        Está função é responsável por iterar pelas linhas de rúbricas do
        holerite e retornar o valor total da linha
        buscando pelo código da rúbrica passada por parâmetro.

        :param codigo: Código (code) da rúbrica a ser pesquisada
        :return: Valor total da linha no holerite
        """
        total_rubrica = 0.00

        for line in self.line_ids:
            if line.code == codigo:
                return line.total

        return total_rubrica

    @profile
    def buscar_porcentagem_pensao(self):
        """
        Função responsável por verificar nas rubricas específicas se existe
        um apontamento de pensao

        :return: Porcentagem da pensão ou 0
        """
        porcentagem_pensao = 0
        for line in self.contract_id.specific_rule_ids:
            if line.rule_id.code in CALCULATED_SPECIFC_RULE:
                porcentagem_pensao = line.specific_amount
                break

        return porcentagem_pensao

    @profile
    def _get_valor_bruto(self, tipo_folha):
        payslip_id = self.search([
            ('tipo_de_folha', '=', tipo_folha),
            ('mes_do_ano', '=', self.mes_do_ano),
            ('ano', '=', self.ano),
            ('contract_id', '=', self.contract_id.id),
        ])

        total_bruto = 0.0

        if payslip_id:
            for line in payslip_id.line_ids:
                if line.salary_rule_id.category_id.code == 'PROVENTO':
                    total_bruto += line.total

        return total_bruto

    @profile
    def get_valor_pensao(self, porcentagem_pensao, locals):
        """
        Função responsável por calcular o valor correto da pensão a partir de
        uma porcentagem do salário líquido do empregado

        :param porcentagem_pensao: Valor em float da porcentagem da pensão
        alimentícia
        :return: Valor total da pensão ou 0
        """

        pensao = 0

        if porcentagem_pensao:
            bruto = locals.get(u'BRUTO', 0)
            inss = 0

            # total_decimo_terceiro = self._get_valor_bruto('decimo_terceiro')

            total_ferias = self._get_valor_bruto('ferias')

            bruto -= total_ferias

            dependent_values = self.get_dependent_values_irrf(self.ano)

            if self.tipo_de_folha in ['normal', 'decimo_terceiro']:
                inss = locals.get(u'INSS', 0)
            else:
                inss = locals.get(u'INSS_COMPETENCIA_ATUAL', 0)

            base_irrf = self.BASE_IRRF(bruto, inss)

            faixa_irrf = self.env['l10n_br.hr.income.tax'].search([
                ('year', '=', self.ano),
                ('max_wage', '<=', base_irrf)
            ], order='max_wage DESC', limit=1)

            aliquota = faixa_irrf.rate
            deducao_irrf = faixa_irrf.deductable

            pensao_porcentagem_decimal = porcentagem_pensao / 100
            aliquota_porcentagem_decimal = aliquota / 100

            # Fórmula utilizada para o pagamento de pensão alimentícia
            # utilizando uma porcentagem em cima do valor
            # liquido dos rendimentos
            # {BRUTO - INSS - [(BRUTO - INSS - DEPENDENTES - PENSAO) * ALIQ_IRRF - DEDUÇAO_IRRF]} * PERC_PENSAO

            valor_1 = bruto - inss
            valor_2 = (bruto - inss - dependent_values) * \
                      aliquota_porcentagem_decimal - deducao_irrf
            valor_3 = (valor_1 - valor_2) * pensao_porcentagem_decimal

            pensao = valor_3 / (1 - (
                    aliquota_porcentagem_decimal * pensao_porcentagem_decimal
            ))

        return pensao, porcentagem_pensao

    @profile
    def get_valor_pensao_adiantamente_decimo_terceiro(self):
        """

        :param locals:
        :return:
        """
        domain = [
            ('tipo_de_folha', 'in', ['decimo_terceiro', 'ferias']),
            ('contract_id', '=', self.contract_id.id),
            ('state', 'in', ['done', 'verify']),
            ('ano', '=', self.ano),
            ('is_simulacao', '=', False),
            ('mes_do_ano', '<=', self.mes_do_ano),
        ]
        holerites = self.search(domain, order='mes_do_ano DESC')

        valor = 0
        if holerites:
            for holerite in holerites:
                for line in holerite.line_ids:
                    if line.code in [
                        'PENSAO_ALIMENTICIA',
                    ]:
                        if not (self.tipo_de_folha == 'ferias'
                                and holerite.mes_do_ano == self.mes_do_ano):
                            valor += line.total

        return valor
